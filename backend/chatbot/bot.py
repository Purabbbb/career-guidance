"""
bot.py
------
PIPELINE STEP 9: Chatbot with Groq API (Llama 3.3) & Keyword Fallback

Architecture:
  1. Groq API — powered by ultra-fast Llama 3 (llama-3.3-70b-versatile).
     Answers career guidance questions contextually using the candidate's resume analysis.

  2. Keyword Intent Classifier — reliable deterministic fallback if GROQ_API_KEY is not set or network fails.

Intent classes (9):
  GREETING, BEST_ROLE, SKILLS, GAP, COURSES, JOBS, PROFILE, SALARY, IMPROVE
"""

import os
import json
import random
import requests
from typing import Optional


def _generate_with_groq(user_message: str, analysis: dict, history: list) -> Optional[dict]:
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        return None

    try:
        entities = analysis.get("entities", {})
        name = entities.get("name", "")
        skills = analysis.get("skills", {}).get("matched_skills", [])
        top_roles = analysis.get("job_roles", {}).get("top_roles", [])
        gaps = analysis.get("gap_analysis", {}).get("missing_skills", [])
        courses = analysis.get("courses", {}).get("recommendations", [])

        roles_summary = ", ".join([f"{r.get('role')} ({r.get('score')}%)" for r in top_roles[:4]]) if top_roles else "Not classified"
        skills_summary = ", ".join(skills[:20]) if skills else "None detected"
        gaps_summary = ", ".join(gaps[:12]) if gaps else "None"
        courses_summary = ", ".join([c.get("title", "") for c in courses[:4]]) if courses else "None"

        system_prompt = f"""You are MargDarshak's AI Career Mentor, an expert career advisor.
Your role is to guide candidates using their verified resume analysis data.

CANDIDATE PROFILE:
- Name: {name or 'Candidate'}
- Top Matched Roles: {roles_summary}
- Skills Detected: {skills_summary}
- Skill Gaps: {gaps_summary}
- Recommended Courses: {courses_summary}

INSTRUCTIONS:
1. Provide concise, clear, encouraging, and direct answers (2 to 4 sentences).
2. Reference their actual skills and matches when relevant.
3. If they ask about next steps, roadmap, or salary, give concrete practical guidance.
4. Keep the tone professional, friendly, and empowering."""

        messages = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history if provided
        if history and isinstance(history, list):
            for h in history[-4:]:
                if isinstance(h, dict) and "role" in h and "content" in h:
                    messages.append({"role": h["role"], "content": h["content"]})

        messages.append({"role": "user", "content": user_message})

        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=15
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            return {
                "response": content,
                "intent": "GROQ_CHAT",
                "confidence": 1.0,
                "method": "groq (llama-3.3-70b-versatile)"
            }
    except Exception as e:
        print(f"[bot.py] Groq request failed: {e}. Falling back to keywords...")
    return None


# ── Keyword fallback classifier (identical to original) ───────────────────────

INTENT_PATTERNS = {
    "BEST_ROLE": [
        "best", "suited", "fit", "match", "role", "career", "job for me",
        "which job", "what job", "recommend", "suggest", "top role", "best match"
    ],
    "SKILLS": [
        "skill", "skills", "know", "have", "technology", "tools", "tech stack",
        "extracted", "found", "detect", "what did you find", "proficient", "strong"
    ],
    "GAP": [
        "missing", "gap", "lack", "not have", "need to learn",
        "should learn", "weak", "add", "acquire", "what is missing"
    ],
    "COURSES": [
        "course", "courses", "learn", "tutorial", "certification", "study",
        "resource", "free", "platform", "where", "how to learn", "training"
    ],
    "JOBS": [
        "job", "jobs", "hiring", "opening", "vacancy", "apply", "listing",
        "company", "work", "position", "opportunity", "find job", "get job"
    ],
    "PROFILE": [
        "name", "email", "phone", "contact", "location", "linkedin", "github",
        "profile", "information", "details", "who am i", "my info"
    ],
    "SALARY": [
        "salary", "pay", "compensation", "package", "ctc", "lpa", "earn",
        "income", "money", "how much"
    ],
    "IMPROVE": [
        "improve", "better", "enhance", "boost", "strengthen", "tips",
        "advice", "guidance", "what should i do", "next step", "roadmap",
        "how to get", "how do i become", "path", "plan"
    ],
    "GREETING": [
        "hello", "hi", "hey", "thanks", "thank you", "great",
        "awesome", "help me", "start", "begin", "okay", "ok"
    ]
}


def _classify_with_keywords(message: str) -> str:
    msg = message.lower().strip()
    scores = {intent: 0 for intent in INTENT_PATTERNS}
    for intent, keywords in INTENT_PATTERNS.items():
        for kw in keywords:
            if kw in msg:
                scores[intent] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "GREETING"


# ── Response handlers ─────────────────────────────────────────────────────────

def handle_greeting(analysis: dict) -> str:
    name = analysis.get("entities", {}).get("name", "")
    best = analysis.get("job_roles", {}).get("best_match", {})
    role = best.get("role", "") if best else ""
    greeting = f"Hello{', ' + name.split()[0] if name else ''}! "
    if role:
        return (
            f"{greeting}I have analyzed your resume. Based on your skills, "
            f"you are a strong candidate for {role}. "
            f"Ask me about your skills, skill gaps, courses, or job listings."
        )
    return f"{greeting}I have analyzed your resume. Ask me anything about your skills, job matches, or career path."


def handle_best_role(analysis: dict) -> str:
    top_roles = analysis.get("job_roles", {}).get("top_roles", [])
    if not top_roles:
        return "No job role analysis available. Please re-upload your resume."
    lines = ["Based on cosine similarity between your skill set and O*NET-aligned role requirements, here are your top matches:\n"]
    for i, role in enumerate(top_roles[:4], 1):
        lines.append(f"{i}. {role['role']} — {role['score']}% match")
    best = top_roles[0]
    lines.append(f"\nYour strongest fit is {best['role']}. {best.get('description', '')}")
    return "\n".join(lines)


def handle_skills(analysis: dict) -> str:
    skills_data = analysis.get("skills", {})
    all_skills = skills_data.get("matched_skills", [])
    by_cat = skills_data.get("by_category", {})
    count = len(all_skills)
    if count == 0:
        return "No skills were detected in your resume. Make sure your resume clearly lists technologies, tools, and frameworks."
    top_cats = list(by_cat.keys())[:4]
    cat_summary = ", ".join([
        f"{k.replace('_', ' ').title()} ({len(by_cat[k])})"
        for k in top_cats
    ])
    sample = ", ".join(all_skills[:12])
    more = f" and {count - 12} more" if count > 12 else ""
    return (
        f"I detected {count} skills across {len(by_cat)} categories.\n\n"
        f"Top categories: {cat_summary}\n\n"
        f"Skills found: {sample}{more}."
    )


def handle_gap(analysis: dict) -> str:
    gaps = analysis.get("gaps", {}).get("gaps", {})
    top_roles = analysis.get("job_roles", {}).get("top_roles", [])
    if not gaps or not top_roles:
        return "No gap analysis available yet."
    best_role = top_roles[0]["role"]
    gap = gaps.get(best_role, {})
    missing_req = gap.get("missing_required", [])
    missing_pref = gap.get("missing_preferred", [])
    readiness = gap.get("readiness_score", 0)
    lines = [f"For your best match — {best_role} — you are {readiness}% ready.\n"]
    if not missing_req and not missing_pref:
        lines.append("You have all required and preferred skills for this role.")
    else:
        if missing_req:
            lines.append(f"Missing required skills ({len(missing_req)}): {', '.join(missing_req)}")
        if missing_pref:
            lines.append(f"Missing preferred skills ({len(missing_pref)}): {', '.join(missing_pref[:5])}")
        lines.append("\nFocus on required skills first — they have the most impact on your candidacy.")
    return "\n".join(lines)


def handle_courses(analysis: dict) -> str:
    courses_data = analysis.get("courses", {})
    priority = courses_data.get("priority_skills", [])
    top_roles = analysis.get("job_roles", {}).get("top_roles", [])
    if not priority:
        return "Your skill gaps are minimal. Check the Courses tab for any remaining recommendations."
    lines = ["Here are the most important skills to learn, in priority order:\n"]
    for i, skill in enumerate(priority[:6], 1):
        lines.append(f"{i}. {skill.title()}")
    lines.append("\nAll recommended courses are free to audit. Check the Courses tab for direct links to Coursera, freeCodeCamp, and official documentation.")
    if top_roles:
        lines.append(f"\nFocusing on these will significantly improve your match for {top_roles[0]['role']}.")
    return "\n".join(lines)


def handle_jobs(analysis: dict) -> str:
    jobs_data = analysis.get("jobs", {})
    job_list = jobs_data.get("jobs", [])
    query = jobs_data.get("query", {})
    status = jobs_data.get("status", "")
    best_role = analysis.get("job_roles", {}).get("best_match", {})
    role_name = best_role.get("role", "your target role") if best_role else "your target role"
    if status == "mock" or not job_list:
        return (
            f"Live job listings require Adzuna API keys in your .env file. "
            f"Once configured, you will see real {role_name} listings filtered by your location. "
            f"You can also search on LinkedIn, Naukri, or Indeed for '{role_name}' roles."
        )
    location = query.get("location", "India")
    lines = [f"I found {jobs_data.get('total_found', len(job_list))} live listings for {role_name} in {location}.\n"]
    for job in job_list[:3]:
        lines.append(f"- {job['title']} at {job['company']} ({job['location']})")
    lines.append("\nCheck the Live Jobs tab to view all listings and apply directly.")
    return "\n".join(lines)


def handle_profile(analysis: dict) -> str:
    e = analysis.get("entities", {})
    lines = ["Here is the contact information extracted from your resume:\n"]
    fields = [
        ("Name", e.get("name")),
        ("Email", e.get("email")),
        ("Phone", e.get("phone")),
        ("Location", e.get("location")),
        ("LinkedIn", e.get("linkedin")),
        ("GitHub", e.get("github")),
    ]
    found = [(k, v) for k, v in fields if v]
    if not found:
        return "No contact information was detected. Make sure your resume has clearly formatted contact details at the top."
    for key, val in found:
        lines.append(f"{key}: {val}")
    missing = [k for k, v in fields if not v]
    if missing:
        lines.append(f"\nNot detected: {', '.join(missing)}")
    return "\n".join(lines)


def handle_salary(analysis: dict) -> str:
    top_roles = analysis.get("job_roles", {}).get("top_roles", [])
    if not top_roles:
        return "No role analysis available to estimate salary ranges."
    role = top_roles[0]["role"]
    salary_map = {
        "Data Scientist": "8 – 25 LPA",
        "Data Analyst": "4 – 12 LPA",
        "Machine Learning Engineer": "12 – 35 LPA",
        "Frontend Developer": "4 – 18 LPA",
        "Backend Developer": "5 – 20 LPA",
        "Full Stack Developer": "6 – 22 LPA",
        "DevOps Engineer": "7 – 25 LPA",
        "Cybersecurity Analyst": "5 – 20 LPA",
        "Mobile App Developer": "4 – 18 LPA",
        "UI/UX Designer": "4 – 16 LPA",
        "Business Analyst": "4 – 15 LPA",
        "Cloud Architect": "15 – 40 LPA",
    }
    sal = salary_map.get(role, "varies based on experience and location")
    score = top_roles[0].get("score", 0)
    return (
        f"For {role} roles in India, typical compensation ranges from {sal}.\n\n"
        f"Factors that influence your specific offer:\n"
        f"- Years of experience\n"
        f"- City (Bangalore, Mumbai, Delhi command a premium)\n"
        f"- Company size — startups vs MNCs\n"
        f"- Your current match score is {score}%, which affects your negotiating position\n\n"
        f"Source: Glassdoor and LinkedIn Salary Insights, India 2024"
    )


def handle_improve(analysis: dict) -> str:
    top_roles = analysis.get("job_roles", {}).get("top_roles", [])
    gaps = analysis.get("gaps", {}).get("gaps", {})
    priority = analysis.get("courses", {}).get("priority_skills", [])
    if not top_roles:
        return "Upload your resume first to get personalized improvement advice."
    best = top_roles[0]
    role = best["role"]
    score = best["score"]
    gap = gaps.get(role, {})
    missing_req = gap.get("missing_required", [])
    lines = [f"Personalized improvement roadmap for {role}:\n"]
    lines.append(f"Current match score: {score}%\n")
    if score >= 80:
        lines.append("You are well-positioned for this role.")
        lines.append("Next steps:")
        lines.append("1. Apply to the live job listings in the Jobs tab")
        lines.append("2. Build 1-2 portfolio projects using your existing skills")
        lines.append("3. Get a relevant certification to strengthen your profile")
    elif score >= 50:
        lines.append("You have a solid base but need to close some gaps.")
        lines.append("Next steps:")
        if missing_req:
            lines.append(f"1. Learn these required skills first: {', '.join(missing_req[:3])}")
        lines.append("2. Build projects that demonstrate your existing skills")
        lines.append("3. Start applying while learning — do not wait until you feel 100% ready")
    else:
        lines.append("You are early in your journey for this role.")
        lines.append("Next steps:")
        if priority:
            lines.append(f"1. Start with: {', '.join(priority[:3])}")
        lines.append("2. Complete one structured course before moving to the next")
        lines.append("3. Build small projects alongside learning")
        lines.append("4. Re-upload your resume after 2-3 months to track your progress")
    return "\n".join(lines)


FALLBACK_RESPONSES = [
    "I can answer questions about your skills, job role matches, skill gaps, courses, or job listings. What would you like to know?",
    "Try asking: 'What is my best job match?', 'Which skills am I missing?', or 'What courses should I take?'",
    "I have your full resume analysis loaded. Ask me about your profile, skills, career path, or how to improve.",
    "You can ask me about salary ranges, missing skills, top job roles, or which courses to start with.",
]

HANDLERS = {
    "GREETING": handle_greeting,
    "BEST_ROLE": handle_best_role,
    "SKILLS":   handle_skills,
    "GAP":      handle_gap,
    "COURSES":  handle_courses,
    "JOBS":     handle_jobs,
    "PROFILE":  handle_profile,
    "SALARY":   handle_salary,
    "IMPROVE":  handle_improve,
}


# ── Main chat function ────────────────────────────────────────────────────────

def chat(user_message: str, analysis: dict, history: list) -> dict:
    """
    Classifies and responds using Groq API (Llama 3.3).
    Falls back to deterministic keyword classifier if GROQ_API_KEY is not set or network fails.

    Args:
        user_message: User input string
        analysis: Full resume analysis dict from /analyze endpoint
        history: Previous messages

    Returns:
        dict with response text, intent, confidence, and method used
    """
    # 1. Try Groq API first
    groq_result = _generate_with_groq(user_message, analysis, history)
    if groq_result:
        return groq_result

    # 2. Deterministic keyword fallback
    intent = _classify_with_keywords(user_message)
    if intent in HANDLERS:
        response = HANDLERS[intent](analysis)
    else:
        response = random.choice(FALLBACK_RESPONSES)

    return {
        "response":   response,
        "intent":     intent,
        "confidence": None,
        "method":     "keyword_fallback"
    }

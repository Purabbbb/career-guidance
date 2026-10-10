"""
roast_engine.py
---------------
SAVAGE, BRUTAL, WITTY, DARK-HUMORED section-by-section resume roaster.

Roasts every section (projects, skills, education, certifications,
internship, objective/summary, experience) with evidence-based,
ugly, yuck, chi, eww-level savagery.

Score: 0-100 (frontend displays as X/10)
"""

import re
import random
from typing import Dict, Any, Optional, List
try:
    from backend.resume_roaster.schemas import RoastResponse, ResumeIssue
    from backend.resume_roaster.scoring import score_resume, WEAK_PHRASES, CLICHE_BUZZWORDS, METRIC_PATTERNS
    from backend.resume_roaster.resume_analyzer import segment_resume_sections
    from backend.resume_roaster.llm_client import LLMClient
except ModuleNotFoundError:
    from resume_roaster.schemas import RoastResponse, ResumeIssue
    from resume_roaster.scoring import score_resume, WEAK_PHRASES, CLICHE_BUZZWORDS, METRIC_PATTERNS
    from resume_roaster.resume_analyzer import segment_resume_sections
    from resume_roaster.llm_client import LLMClient


# ─────────────────────────────────────────────────────────────────────────────
# BRUTAL SECTION ROAST POOLS  (witty, dark, ugly, eww, chi, yuck, savage)
# ─────────────────────────────────────────────────────────────────────────────

_SECTION_ROAST_POOL: Dict[str, List[str]] = {

    "summary": [
        "🤮 This 'Summary' is so packed with buzzwords it gave me a headache and possibly a rash. 'Passionate', 'hardworking', 'team player' — eww, chi, every recruiter's nightmare in one paragraph.",
        "💀 Oh honey. 'Results-driven professional with a passion for excellence'? I've seen more personality on a tax form. This summary is the resume equivalent of lukewarm tap water — technically exists, utterly forgettable.",
        "🤢 Your objective section is a graveyard of clichés. 'Seeking a challenging role to utilise my skills' — challenging for WHO? Certainly not the recruiter who threw up a little reading this.",
        "😬 The audacity. You opened with 'I am a hardworking individual' — congratulations, you've described the bare minimum for being employed. Actual serial killers have more compelling summaries.",
        "🙈 This summary is yuck. Pure, distilled yuck. You've used 4 buzzwords in 2 sentences. That's a personal record for meaninglessness. Even LinkedIn templates are embarrassed for you.",
        "☠️ 'Dynamic professional' — oh WOW. Nobody has ever called themselves dynamic on a resume and been dynamic. It's scientifically impossible. This opening is so generic it could belong to literally anyone on Earth.",
    ],

    "objective": [
        "🤮 An 'Objective' section? In this economy? In this YEAR? Chi chi chi. Nobody has cared about objective sections since 2009. This is a fossil on your resume.",
        "😭 'To obtain a position where I can grow professionally' — grow into WHAT? A better resume writer? Because that's urgently needed. This objective tells me nothing except that you want a job. Shocking revelation.",
        "🤢 Your objective is so vague it could be on a kindergartner's resume. 'To work in a challenging environment' — sweetheart, have you SEEN the job market? Challenge is guaranteed. Put something useful here or delete it.",
        "💀 Ewww. This objective section is the résumé equivalent of showing up to a job interview and saying 'I want money'. DELETE. IT. NOW.",
    ],

    "experience": [
        "🤮 'Responsible for...' — RESPONSIBLE FOR? Chi. Every single bullet starts with the most passive, soul-sucking phrase in corporate history. You didn't DO anything, things just... happened near you?",
        "😤 Your experience bullets are a crime scene. 'Worked on various tasks' — what tasks? For whom? Why should anyone care? This is so vague it's basically a cover-up. What are you HIDING?",
        "💀 Yuck. Not one number. Not one metric. Not one shred of evidence that anything you did mattered. 'Assisted with development' — assisted? You ASSISTED? Not led, not built, not delivered — ASSISTED? Eww.",
        "🤢 'Participated in team meetings' is literally on this resume as an achievement. Baby. Sweetheart. Pumpkin. Showing up to meetings is not an accomplishment. It is the absolute floor of professional existence.",
        "😬 These bullets describe someone hovering near a job, not doing one. 'Helped with database management' — you HELPED? Did you hold someone's hand while they did the real work? This is career fiction.",
        "☠️ The experience section smells like passive voice and desperation. Every verb is weak, every result is missing, every impact is invisible. Recruiters won't read past the second bullet. Honestly? Fair.",
    ],

    "projects": [
        "🤮 'Built a to-do app.' CHI CHI CHI. Your MAGNUM OPUS is a to-do app? The default project of every person who completed a 3-hour YouTube tutorial? Ma'am/Sir, this is a Wendy's.",
        "😭 No numbers. No users. No GitHub link. No deployment. No evidence this project exists outside your laptop and your imagination. Projects without proof are just bedtime stories for your resume.",
        "🤢 'Created a machine learning model' — for what? Trained on what? Achieving what accuracy? 'Model' isn't a project, it's a notebook you ran once and never opened again. Ewww.",
        "💀 Every project here sounds like a renamed tutorial. 'E-commerce website using HTML/CSS' — chi. Did you copy-paste this from a Udemy assignment? Because it reads like it. Show something real or show nothing.",
        "😤 Your projects are so vague they could be evidence in a fraud investigation. 'Developed a web application' — WHAT application? For WHOM? DOING WHAT? This is the most withholding resume in history.",
        "☠️ Yuck. No live link. No GitHub. No deployment. No nothing. It's like describing a meal you allegedly cooked but ate all the evidence. These projects are ghosts — technically 'listed' but provably nonexistent.",
        "🤮 'Built a chatbot using Python' with zero metrics, zero users, zero anything. Congratulations, you've replicated a Hello World with an API key. Your recruiter is already asleep.",
    ],

    "skills": [
        "🤮 Fifty-three skills? FIFTY-THREE? Chi chi chi chi chi. You've listed 'Microsoft Word' next to 'Machine Learning' and thought nobody would notice. This is not a skills section, this is a panic attack in bullet form.",
        "😭 'Python (Beginner), Java (Beginner), C++ (Beginner), JavaScript (Beginner)' — eww. You're a beginner at EVERYTHING. Collectively, these skills amount to someone who has opened four textbooks and closed them.",
        "🤢 Your skills section is longer than your experience section. That is NOT the flex you think it is. It means you have more things you can't do well than things you've actually done.",
        "💀 'Communication skills' is listed under Technical Skills. COMMUNICATION. On a TECHNICAL SKILLS section. The audacity. The absolute soggy audacity of this resume.",
        "😬 You've listed 'Teamwork' as a skill. A SKILL. Like you had to LEARN it. Like 'yeah, I went to teamwork bootcamp, very competitive program, only 300 million people worldwide completed it.'",
        "☠️ Yuck. This is a skill vomit. You've listed every technology you've ever seen a YouTube thumbnail about. Recruiters who see this don't think 'impressive breadth' — they think 'doesn't know what they're doing.'",
        "🤮 'Familiar with AWS' — familiar. Like you've met it at a party once. 'Exposure to Docker' — exposure, like it's a disease you briefly caught. These aren't skills, these are confessions.",
    ],

    "education": [
        "🤮 CGPA: conveniently missing. Chi. We see you. If your grades were good, they'd be here. The absence of a GPA on a resume speaks louder than the one you're hiding.",
        "😭 A degree listing with zero coursework, zero projects, zero extracurriculars, zero achievements. Just 'B.Tech Computer Science, 2024.' Might as well say 'I attended. Sometimes.'",
        "🤢 You spent 4 years in an engineering college and the only proof is a degree name and a year. No relevant coursework. No academic projects. No nothing. Did you go to class or just to the cafeteria?",
        "💀 Ewww. '7.2 CGPA' front and center when you have no projects, no skills in context, and no experience. The CGPA is the only number on this entire resume and it's not even good. Bold strategy.",
        "😬 Education: present. Evidence you learned anything: absent. Your degree is listed like a participation trophy — technically real, impressively meaningless without context.",
    ],

    "certifications": [
        "🤮 Three AWS certifications and zero AWS projects. CHI. You passed multiple choice questions about cloud infrastructure but you've never actually deployed anything. That's not a certification, that's a hobby.",
        "😭 'Udemy Certification: The Complete Python Bootcamp' — baby. Udemy certificates are free with a promo code and auto-generated. This is not a credential. This is a receipt.",
        "🤢 Ewww. You've listed 5 certifications with no projects to show you applied any of them. Certifications are proof you can pass a test. Projects are proof you can do the work. One of those matters to employers.",
        "💀 Coursera completion certificate, LinkedIn Learning badge, and a Google Analytics certification — in the same section as professional credentials. Chi chi chi. One of these things is not like the others.",
        "😤 The certifications section contains 4 certificates from 2020, all in technologies your experience section has never mentioned. You certified in things you've apparently never used. Impressive commitment to irrelevance.",
    ],

    "internship": [
        "🤮 'Intern at ABC Technologies' with the single bullet: 'Worked on software development tasks.' I'm going to need you to sit down. WHAT tasks? WHAT software? WHAT did you develop? This is an internship description as told by someone who slept through it.",
        "😭 Your internship lasted 2 months and contributed 1 bullet point that says nothing. That is a very expensive way to get a blank line on your resume. What did you actually DO there — photocopying?",
        "🤢 Ewwww. 'Gained exposure to industry practices' — GAINED EXPOSURE. Like a potted plant near a window. This is not experience, this is a very expensive shadow-following exercise.",
        "💀 Internship with no outcomes, no technologies named, no projects delivered. Just duration and company name. Congratulations, you've proven you can sign an internship agreement. The bar was underground and you dug.",
        "😬 Chi. Your internship bullets read like they were written by someone who did very little and then tried to make it sound like more by using long sentences. It did not work.",
    ],

    "achievements": [
        "🤮 'Won 3rd prize in college hackathon 2021' is your top achievement. CHI CHI CHI. Third place. In your college. In 2021. This is the achievement equivalent of a participation trophy that lost a fight.",
        "😭 The achievements section is just your certification list renamed. Ewww. Passing a course is not an achievement. Getting a certificate is not an achievement. Deploying something that works — THAT would be an achievement.",
        "🤢 'Completed 30 days coding challenge' — absolutely unhinged that this made the cut. You coded for 30 days and it's your biggest flex. What happened on day 31? Did you retire?",
        "💀 Your achievements section reads like a LinkedIn post that got 3 likes from college friends. Every item is self-congratulatory and exactly zero of them will impress a hiring manager.",
    ],

    "hobbies": [
        "🤮 'Hobbies: Reading, Travelling, Listening to Music' — CHI. You've described 3 billion people. This adds literally zero value to a professional resume. Delete it. Burn it. Never speak of it.",
        "😭 You used resume space — PRECIOUS, LIMITED resume space — to tell a hiring manager you enjoy travelling. Ma'am/Sir, every human alive enjoys travelling. This is not a personality, it is oxygen.",
        "🤢 Ewww. 'Cricket and Badminton' as hobbies on a tech resume. Are you applying for a job or a sports team? Unless your sport is directly relevant, this space should be occupied by literally anything else.",
    ],

    "general": [
        "🤮 This resume has the structural integrity of wet tissue paper. Sections unlabeled, bullets scattered, formatting inconsistent. Recruiters spend 6 seconds on a resume. This one wasted 3 of them on confusion.",
        "😭 Chi. The formatting alone is a war crime. Inconsistent fonts, random capitalization, bullet points that go nowhere. This resume is what happens when someone discovers Word but never learns it.",
        "🤢 Ewwwww. This looks like it was formatted during a power cut. The layout fights itself, the spacing is aggressive, and the overall effect is 'I did not think anyone would actually read this.'",
        "💀 Your resume is an archaeological dig — layers of bad decisions, unclear sections, and the ghost of a template you abandoned halfway through. Recruiters don't excavate, they skip.",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE-BASED ISSUE GENERATOR  (per section, per detected problem)
# ─────────────────────────────────────────────────────────────────────────────

def _roast_pool(section: str) -> List[str]:
    key = section.lower()
    for k in _SECTION_ROAST_POOL:
        if k in key or key in k:
            return _SECTION_ROAST_POOL[k]
    return _SECTION_ROAST_POOL["general"]


def _analyze_section_deep(
    section_name: str,
    section_text: str,
    issue_counter: int,
) -> List[ResumeIssue]:
    """
    Deep, evidence-based issue detection for a single resume section.
    Produces BRUTAL, SPECIFIC issues grounded in actual text.
    """
    issues: List[ResumeIssue] = []
    text_lower = section_text.lower()
    lines = [l.strip() for l in section_text.split("\n") if l.strip()]

    sec = section_name.lower()

    # ── SUMMARY / OBJECTIVE ──────────────────────────────────────────────────
    if sec in ("summary", "objective", "general"):
        for pat in CLICHE_BUZZWORDS:
            m = re.search(pat, text_lower)
            if m:
                word = m.group(0)
                issues.append(ResumeIssue(
                    id=f"issue_{issue_counter}",
                    section=section_name,
                    severity="high",
                    category="cliché_buzzwords",
                    evidence=f'"{word}"',
                    roast=f"Chi chi chi — '{word}'?? Every fresh-out-of-college resume has this exact word. It means absolutely nothing. A recruiter's eyes just glazed over and died.",
                    why_it_matters="Overused adjectives are filtered out by both ATS software and human recruiters within the first 3 seconds.",
                    suggestion=f"Delete '{word}' entirely. Replace with a specific technical stack, years of experience, or a measurable achievement.",
                    rewrite_example="Python backend engineer with 2 years building REST APIs and microservices for 50K+ user platforms."
                ))
                issue_counter += 1
                break

        word_count = len(section_text.split())
        if word_count < 20:
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="medium",
                category="weak_impact",
                evidence=f"Only {word_count} words in summary",
                roast=f"Ewww. Your summary is {word_count} words long. That's not a summary, that's a caption. You have ONE shot to hook a recruiter and you used it to write a haiku about nothing.",
                why_it_matters="A compelling summary is 3-4 sentences with specific skills, experience, and value proposition.",
                suggestion="Write 3-4 lines: your title, your top tech stack, years of experience, and what kind of problems you solve.",
                rewrite_example="Full-stack developer with 3 years building scalable web apps in React + FastAPI. Deployed to 20K+ users. Strong in system design, API architecture, and database optimization."
            ))
            issue_counter += 1

    # ── EXPERIENCE ────────────────────────────────────────────────────────────
    if sec == "experience":
        passive_count = 0
        for line in lines:
            for pat in WEAK_PHRASES:
                if re.search(pat, line, re.IGNORECASE):
                    snippet = line[:80] + ("..." if len(line) > 80 else "")
                    issues.append(ResumeIssue(
                        id=f"issue_{issue_counter}",
                        section=section_name,
                        severity="high",
                        category="passive_voice",
                        evidence=snippet,
                        roast=f"Yuck. '{snippet[:50]}...' — you were RESPONSIBLE FOR things. Things didn't get done BECAUSE OF you, they just... happened while you were in the room. This is passive voice and it's vomit-inducing on a resume.",
                        why_it_matters="ATS and recruiters rank active-voice, outcome-driven bullets 3x higher than passive task descriptions.",
                        suggestion="Start with a strong action verb and end with a result or number.",
                        rewrite_example="Engineered REST API handling 10K daily requests, reducing response latency by 40%."
                    ))
                    issue_counter += 1
                    passive_count += 1
                    break
            if passive_count >= 2:
                break

        has_metric = any(re.search(p, section_text, re.IGNORECASE) for p in METRIC_PATTERNS)
        if not has_metric and lines:
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="high",
                category="missing_metrics",
                evidence="Zero numbers in entire experience section",
                roast="ZERO numbers. NOT ONE. In your ENTIRE experience section. Chi chi chi. How long did you work there? How many users? How much faster? How many bugs? NOTHING. Your impact is completely invisible and frankly so are you.",
                why_it_matters="Resumes with quantified achievements are 40% more likely to land interviews according to recruiting studies.",
                suggestion="Add at least one number to each bullet: team size, user count, % improvement, or time saved.",
                rewrite_example="Reduced API response time by 35% by optimizing 12 database queries, supporting 5K+ concurrent users."
            ))
            issue_counter += 1

    # ── PROJECTS ─────────────────────────────────────────────────────────────
    if sec == "projects":
        has_metric = any(re.search(p, section_text, re.IGNORECASE) for p in METRIC_PATTERNS)
        if not has_metric and lines:
            sample = lines[0][:80] if lines else "your project"
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="high",
                category="weak_impact",
                evidence=sample,
                roast=f"Ewwww. '{sample[:60]}' — no numbers, no scale, no link, no proof it ever ran. Is this a project or a fever dream you had? Add EVIDENCE or delete it.",
                why_it_matters="Projects without metrics, links, or scale are indistinguishable from tutorial exercises.",
                suggestion="Add the tech stack, dataset size, user count, accuracy, or a GitHub/live link to every project.",
                rewrite_example="Sentiment classifier on 50K tweets using BERT — 89% accuracy, deployed on HuggingFace, 200+ demo users."
            ))
            issue_counter += 1

        # Check for tutorial-sounding project names
        tutorial_patterns = [r"\btodo\b", r"\bto-do\b", r"\bcalculator\b", r"\bweather app\b", r"\bportfolio\b", r"\bchat app\b"]
        for pat in tutorial_patterns:
            if re.search(pat, text_lower):
                issues.append(ResumeIssue(
                    id=f"issue_{issue_counter}",
                    section=section_name,
                    severity="medium",
                    category="weak_impact",
                    evidence=f"Tutorial-level project detected in Projects section",
                    roast="Chi chi chi. A todo/weather/calculator app. THE tutorial project. The one every person alive has built after their first YouTube video. This is not a project, this is a timestamp of when you discovered coding. Replace it.",
                    why_it_matters="Entry-level tutorial projects signal no real-world problem-solving experience to recruiters.",
                    suggestion="Replace with a project that solves a real problem, has real users, or demonstrates a complex technical decision.",
                    rewrite_example="Built a real-time traffic routing API using Dijkstra's algorithm — 3ms average latency, 500 req/s load tested."
                ))
                issue_counter += 1
                break

    # ── SKILLS ───────────────────────────────────────────────────────────────
    if sec == "skills":
        skill_count = len([l for l in lines if l])
        # Count comma-separated skills too
        all_skills_text = section_text.replace("\n", ",")
        approx_count = max(skill_count, len([s for s in all_skills_text.split(",") if s.strip()]))

        if approx_count > 20:
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="high",
                category="skill_dump",
                evidence=f"~{approx_count} skills listed",
                roast=f"YUCK. {approx_count} skills? CHI CHI CHI. You've turned your skills section into a technology landfill. Recruiters don't see depth — they see someone who Googled 'list of programming languages' and copy-pasted it. This is embarrassing.",
                why_it_matters="Skill dumps signal lack of focus and often get lower ATS scores than targeted, context-backed skill lists.",
                suggestion="Keep 8-12 skills you can actually defend in an interview. Group them: Languages, Frameworks, Tools, Cloud.",
                rewrite_example="Languages: Python, JavaScript | Frameworks: FastAPI, React | Cloud: AWS (EC2, S3, Lambda) | Tools: Docker, Git"
            ))
            issue_counter += 1

        # Look for beginner/familiar qualifiers
        if re.search(r"\b(beginner|familiar|basic|exposure|learning|aware)\b", text_lower):
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="high",
                category="weak_proficiency",
                evidence="Qualifiers like 'beginner', 'familiar', 'exposure' found",
                roast="Ewwwww. You've voluntarily labelled yourself a beginner. ON YOUR OWN RESUME. You've pre-rejected yourself. A recruiter reading 'beginner Python' is already closing the tab. If you can't defend it in an interview, don't list it.",
                why_it_matters="Self-deprecating skill qualifiers signal unpreparedness and often cause automatic ATS filtering.",
                suggestion="Only list skills you can code with for 15 minutes in an interview without Googling. Remove the rest.",
                rewrite_example="Python (REST APIs, Pandas, Scikit-learn) | JavaScript (React, Node.js) | SQL (PostgreSQL, query optimization)"
            ))
            issue_counter += 1

        # Soft skills in a technical skills section
        soft_skills = ["communication", "teamwork", "leadership", "problem solving", "time management", "adaptability"]
        for soft in soft_skills:
            if soft in text_lower:
                issues.append(ResumeIssue(
                    id=f"issue_{issue_counter}",
                    section=section_name,
                    severity="medium",
                    category="cliché_buzzwords",
                    evidence=f"Soft skill listed: '{soft}'",
                    roast=f"Chi. '{soft.title()}' is listed as a skill. As if you had to TRAIN for it. As if there's a '{soft.title()} Bootcamp' you graduated from. This adds zero value and makes you look like you ran out of real things to say.",
                    why_it_matters="Soft skills in a technical skills section occupy space and signal lack of technical depth to recruiters.",
                    suggestion=f"Delete '{soft}' from your skills. If you want to show {soft}, demonstrate it through your project descriptions or experience bullets.",
                    rewrite_example="Delivered cross-functional API integration with 3 teams, shipped on time under a 2-week deadline."
                ))
                issue_counter += 1
                break

    # ── EDUCATION ────────────────────────────────────────────────────────────
    if sec == "education":
        if not re.search(r"\b\d+\.?\d*\s*(cgpa|gpa|%|percent|grade)\b", text_lower):
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="medium",
                category="missing_info",
                evidence="No GPA/CGPA found in education section",
                roast="CGPA: [suspiciously absent]. Chi. We see what you did there. If your grades were something to be proud of, they'd be here. The missing CGPA is speaking volumes, and none of it is good.",
                why_it_matters="For freshers and recent graduates, CGPA is a key screening factor for many companies.",
                suggestion="Include your CGPA if it's above 7.0. If it's below, add relevant certifications and strong projects to compensate.",
                rewrite_example="B.Tech Computer Science — XYZ University | CGPA: 8.4/10 | 2024"
            ))
            issue_counter += 1

    # ── CERTIFICATIONS ───────────────────────────────────────────────────────
    if sec == "certifications":
        udemy_pats = [r"\budemy\b", r"\bcorsera\b", r"\bcoursera\b", r"\blinkedin learning\b", r"\byoutube\b"]
        for pat in udemy_pats:
            if re.search(pat, text_lower):
                platform = pat.replace(r"\b", "").strip()
                issues.append(ResumeIssue(
                    id=f"issue_{issue_counter}",
                    section=section_name,
                    severity="medium",
                    category="weak_credentials",
                    evidence=f"Platform: {platform}",
                    roast=f"Ewwww. A {platform.title()} certificate. Baby. These are $10 during sales and auto-issued to anyone who clicks through the videos. This is not a credential, this is a watching-videos certificate. It does not impress anyone past entry level.",
                    why_it_matters="Free/cheap online certificates carry very little weight compared to projects, contributions, or accredited certifications.",
                    suggestion="Replace with industry-recognised certs (AWS, GCP, Azure, Google) or — better — add a project that proves you can apply the knowledge.",
                    rewrite_example="AWS Certified Developer – Associate | Deployed 3 production services on EC2 + Lambda (GitHub: github.com/...)"
                ))
                issue_counter += 1
                break

    # ── INTERNSHIP ───────────────────────────────────────────────────────────
    if sec in ("internship", "internships"):
        has_metric = any(re.search(p, section_text, re.IGNORECASE) for p in METRIC_PATTERNS)
        if not has_metric and lines:
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="high",
                category="missing_metrics",
                evidence=lines[0][:80] if lines else "Internship with no outcomes",
                roast="Chi chi chi. Your internship contributed exactly zero measurable outcomes to this resume. What did you BUILD? What did you IMPROVE? What did you DELIVER? 'Worked on software tasks' is not an internship, it's a paid nap.",
                why_it_matters="Internship bullets without outcomes are equivalent to blank space — they take up room without adding value.",
                suggestion="Add what you built, what technologies you used, and ideally a result (pages served, latency improved, bugs fixed).",
                rewrite_example="Built REST API for inventory module using Flask + PostgreSQL — reduced manual data entry time by 60% for 5-person ops team."
            ))
            issue_counter += 1

    # ── ACHIEVEMENTS ─────────────────────────────────────────────────────────
    if sec == "achievements":
        college_hackathon = re.search(r"\b(hackathon|competition|contest)\b", text_lower)
        if college_hackathon:
            issues.append(ResumeIssue(
                id=f"issue_{issue_counter}",
                section=section_name,
                severity="low",
                category="weak_impact",
                evidence="College hackathon/competition mentioned",
                roast="Ewww. A college hackathon from 3 years ago. Is this the peak? The summit of professional achievement? Unless it was a national/international competition with 500+ teams, this is taking up space that could be used for literally anything more impressive.",
                why_it_matters="College hackathons lose relevance quickly. After your first real project or internship, they should be replaced.",
                suggestion="Replace with quantified professional achievements, deployed projects, or open-source contributions.",
                rewrite_example="Open-source contributor to FastAPI (GitHub: 47⭐ personal repo) | National-level Smart India Hackathon finalist 2023"
            ))
            issue_counter += 1

    # ── HOBBIES ──────────────────────────────────────────────────────────────
    if sec in ("hobbies", "interests", "personal"):
        boring_hobbies = [r"\breading\b", r"\btravell?ing\b", r"\blistening to music\b", r"\bcricket\b", r"\bbadminton\b", r"\bwatching movies\b"]
        for pat in boring_hobbies:
            if re.search(pat, text_lower):
                issues.append(ResumeIssue(
                    id=f"issue_{issue_counter}",
                    section=section_name,
                    severity="low",
                    category="irrelevant",
                    evidence=section_text[:60],
                    roast="CHI. You've used premium resume real estate to tell a software engineer recruiter that you enjoy... reading and travelling. So does every single person on the planet. DELETE this section unless your hobby is directly relevant (open source, competitive programming, technical writing).",
                    why_it_matters="Generic hobbies add zero value to a technical resume and waste space that could show skills or projects.",
                    suggestion="Delete entirely, OR replace with relevant technical activities: competitive programming, open-source contributions, technical blogging.",
                    rewrite_example="Technical blogger (dev.to/yourhandle — 2K monthly readers) | Competitive programmer (Codeforces: 1500 rating)"
                ))
                issue_counter += 1
                break

    return issues


def _generate_opening_roast(sections: Dict[str, str], all_issues: List[ResumeIssue]) -> str:
    """Generate a savage opening one-liner based on overall resume state."""

    total_issues = len(all_issues)
    has_projects = bool(sections.get("projects", "").strip())
    has_metrics = any(
        re.search(p, " ".join(sections.values()), re.IGNORECASE)
        for p in METRIC_PATTERNS
    )
    has_buzzwords = any(
        re.search(p, " ".join(sections.values()), re.IGNORECASE)
        for p in CLICHE_BUZZWORDS
    )
    skill_text = sections.get("skills", "")
    skill_count = len([s for s in skill_text.replace("\n", ",").split(",") if s.strip()])

    openers = []

    if skill_count > 20 and not has_metrics:
        openers.append(
            f"🤮 {skill_count} skills listed. Zero measurable outcomes anywhere. This resume has the width of an ocean and the depth of a puddle. Chi chi chi."
        )
    if not has_projects:
        openers.append(
            "💀 No projects section. In a SOFTWARE RESUME. In 2025. The audacity of applying for a tech job with zero proof you have ever actually built anything is genuinely breathtaking."
        )
    if has_buzzwords and not has_metrics:
        openers.append(
            "🤢 Packed with 'passionate', 'hardworking', 'team player' — and completely empty of any actual numbers or evidence. Ewww. This resume is all costume, no character."
        )
    if total_issues >= 6:
        openers.append(
            f"☠️ {total_issues} issues detected. This resume is not just bad — it's committed to being bad. Every section has found a unique way to fail. That's almost impressive."
        )
    if not has_metrics:
        openers.append(
            "😤 Not a single number on this entire resume. Not one percentage. Not one user count. Not one improvement metric. Your impact is completely invisible. Recruiters can't hire a ghost."
        )

    # fallback
    openers += [
        "🔥 This resume tried its best. Its best was not enough. Let's get into exactly why.",
        "💀 Buckle up. This is going to hurt. But it's going to hurt less than being ghosted by 47 companies in a row.",
        "🤮 I've seen resumes. I've seen bad resumes. This one is special. Let's discuss.",
    ]

    return random.choice(openers)


def _generate_closing_verdict(all_issues: List[ResumeIssue], sections: Dict[str, str]) -> str:
    """Generate the brutal final verdict."""

    has_metrics = any(
        re.search(p, " ".join(sections.values()), re.IGNORECASE)
        for p in METRIC_PATTERNS
    )

    verdicts = [
        "The fix is not complicated: every bullet needs a number, every project needs a link, every buzzword needs to die. Do that and this resume becomes hireable.",
        "Your resume is currently a liability. With real numbers and active verbs, it becomes an asset. The gap between where you are and where you need to be is 2 focused hours of rewriting.",
        "Come back when your bullets prove outcomes, your projects have links, and 'passionate' has been deleted from every file on your computer.",
        "You didn't fail this resume. The resume failed you — because you wrote it like nobody would actually read it. Someone will. Rewrite it like they will.",
        "The bones are okay. The flesh is rotten. Strip it back, add numbers, add links, delete the corporate word salad, and this becomes a real resume.",
    ]
    if not has_metrics:
        verdicts.append("One rule: every bullet that doesn't have a number doesn't belong on this resume. Follow that rule and 80% of the damage fixes itself.")

    return random.choice(verdicts)


class RoastEngine:
    def __init__(self):
        self.llm = LLMClient()

    def roast_resume(
        self,
        resume_text: str,
        analysis_context: Optional[Dict[str, Any]] = None
    ) -> RoastResponse:
        """
        Full SAVAGE, section-by-section roast.
        Every section gets brutally reviewed based on actual content.
        """

        # 1. Scoring
        scores = score_resume(resume_text=resume_text, target_role="Generic")

        # 2. Segment resume into sections
        sections = segment_resume_sections(resume_text)

        # 3. Also detect internship, certifications, achievements, hobbies
        #    that the basic segmenter might miss
        extra_section_patterns = {
            "internship": [r"\binternship\b", r"\bintern\b"],
            "certifications": [r"\bcertification\b", r"\bcertificate\b", r"\bcertified\b"],
            "achievements": [r"\bachievement\b", r"\baward\b", r"\bhonour\b", r"\bhonor\b"],
            "hobbies": [r"\bhobb\b", r"\binterest\b", r"\bpersonal\b"],
            "objective": [r"\bobjective\b", r"\bcareer goal\b"],
        }
        # Scan raw text for extra sections not caught by segmenter
        text_lines = resume_text.split("\n")
        current_extra = None
        extra_content: Dict[str, List[str]] = {}
        for line in text_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if len(stripped.split()) <= 4:
                for sec_name, patterns in extra_section_patterns.items():
                    for p in patterns:
                        if re.search(p, stripped, re.IGNORECASE):
                            current_extra = sec_name
                            extra_content.setdefault(sec_name, [])
                            break
                    if current_extra and sec_name == current_extra:
                        break
            elif current_extra:
                extra_content[current_extra].append(stripped)

        for sec_name, content_lines in extra_content.items():
            if content_lines and sec_name not in sections:
                sections[sec_name] = "\n".join(content_lines)

        # 4. Deep per-section issue analysis
        all_issues: List[ResumeIssue] = []
        issue_counter = 1
        section_order = [
            "summary", "objective", "experience", "internship", "projects",
            "skills", "education", "certifications", "achievements", "hobbies", "general"
        ]
        # Sort sections so important ones come first
        ordered_sections = {}
        for key in section_order:
            if key in sections:
                ordered_sections[key] = sections[key]
        for key in sections:
            if key not in ordered_sections:
                ordered_sections[key] = sections[key]

        for sec_name, sec_text in ordered_sections.items():
            if not sec_text.strip():
                continue
            sec_issues = _analyze_section_deep(sec_name.title(), sec_text, issue_counter)
            issue_counter += len(sec_issues)
            all_issues.extend(sec_issues)

        # 5. Build per-section brutal one-liner roasts
        section_roasts: Dict[str, str] = {}
        for sec_name, sec_text in ordered_sections.items():
            if sec_text.strip():
                pool = _roast_pool(sec_name)
                section_roasts[sec_name.lower()] = random.choice(pool)

        # 6. Opening roast and closing verdict
        opening = _generate_opening_roast(sections, all_issues)
        verdict = _generate_closing_verdict(all_issues, sections)

        # 7. Top fixes
        fixes = []
        for issue in all_issues:
            if issue.suggestion and len(fixes) < 5:
                fixes.append(issue.suggestion)

        return RoastResponse(
            status="success",
            overall_score=scores.overall_score,
            tone="savage",
            headline_roast=opening,
            summary=verdict,
            issues=all_issues,
            section_scores=scores,
            section_roasts=section_roasts,
            top_fixes=fixes[:5],
            ats_keywords_to_consider=[],
            revised_sections={},
            method="MargDarshak BRUTAL Section-by-Section Roast Engine v2"
        )

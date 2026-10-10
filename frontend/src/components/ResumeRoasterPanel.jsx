import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { roastResume } from '../utils/api.js'
import styles from './ResumeRoasterPanel.module.css'

/**
 * Resume Roaster Panel - SAVAGE Edition
 *
 * Supports: PDF, JPG, JPEG, PNG, WEBP
 * Always SAVAGE. No role selector. No tone selector.
 * Scores resume out of 10. Roasts every section.
 */

const LOADING_MESSAGES = [
  'Reading your resume without mercy...',
  'Identifying the worst crimes against formatting...',
  'Analyzing passive voice density...',
  'Calculating the bewilderment index...',
  'Preparing your brutal verdict...',
  'Sharpening the roast...',
]

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/webp': ['.webp'],
}

const SECTION_SCORE_LABELS = {
  structure: 'Structure',
  clarity: 'Clarity',
  impact: 'Impact',
  ats_alignment: 'ATS Fit',
  skill_evidence: 'Skills',
  role_relevance: 'Relevance',
  conciseness: 'Conciseness',
}

const SECTION_ICONS = {
  structure: '🏗️',
  clarity: '💬',
  impact: '💥',
  ats_alignment: '🤖',
  skill_evidence: '🛠️',
  role_relevance: '🎯',
  conciseness: '✂️',
}

/** Convert 0-100 score to /10 (1 decimal) */
function toTen(val) {
  return (Math.round((val / 10) * 10) / 10).toFixed(1)
}

/** Color grade for a 0-10 score */
function scoreColor(score10) {
  const n = parseFloat(score10)
  if (n >= 8) return '#10b981'   // green
  if (n >= 6) return '#f59e0b'   // amber
  if (n >= 4) return '#f97316'   // orange
  return '#ef4444'               // red
}

/** Emoji verdict for overall score */
function scoreVerdict(score10) {
  const n = parseFloat(score10)
  if (n >= 8.5) return 'Impressive'
  if (n >= 7)   return 'Decent'
  if (n >= 5)   return 'Needs Work'
  if (n >= 3)   return 'Struggling'
  return 'Help.'
}

function getFileIcon(name) {
  if (!name) return '📄'
  const ext = name.split('.').pop().toLowerCase()
  if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) return '🖼️'
  return '📄'
}

export default function ResumeRoasterPanel({ analysis, resumeFile }) {
  const [currentFile, setCurrentFile] = useState(resumeFile || null)
  const [loadingRoast, setLoadingRoast] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [error, setError] = useState(null)
  const [roastData, setRoastData] = useState(null)
  const changeFileRef = useRef(null)

  useEffect(() => {
    if (resumeFile && !currentFile) setCurrentFile(resumeFile)
  }, [resumeFile])

  // Handle "Change File" native input (bypasses dropzone when file already loaded)
  function handleChangeFileInput(e) {
    const f = e.target.files?.[0]
    if (!f) return
    const allowed = ['application/pdf','image/jpeg','image/png','image/webp']
    const ext = f.name.split('.').pop().toLowerCase()
    const allowedExt = ['pdf','jpg','jpeg','png','webp']
    if (!allowed.includes(f.type) && !allowedExt.includes(ext)) {
      setError('Unsupported file type. Use PDF, JPG, JPEG, PNG, or WEBP.')
      return
    }
    setError(null)
    setRoastData(null)
    setCurrentFile(f)
    // reset input so same file can be re-selected
    e.target.value = ''
  }

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError(null)
    if (rejectedFiles.length > 0) {
      setError('Unsupported file type. Upload a PDF, JPG, JPEG, PNG, or WEBP resume.')
      return
    }
    if (acceptedFiles.length > 0) {
      setRoastData(null)
      setCurrentFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
  })

  async function handleRoast() {
    if (!currentFile) {
      setError('Please select your resume (PDF or image) to get roasted.')
      return
    }
    setLoadingRoast(true)
    setError(null)
    setLoadingStep(0)

    const interval = setInterval(() => {
      setLoadingStep(prev => (prev < LOADING_MESSAGES.length - 1 ? prev + 1 : prev))
    }, 1500)

    try {
      const data = await roastResume(currentFile, analysis)
      clearInterval(interval)
      setRoastData(data)
    } catch (err) {
      clearInterval(interval)
      setError(err.response?.data?.detail || err.message || 'Failed to roast resume. Please check if backend is running.')
    } finally {
      setLoadingRoast(false)
    }
  }

  // ─── LANDING ──────────────────────────────────────────────
  if (!roastData && !loadingRoast) {
    return (
      <div className={styles.container}>
        <div className={styles.landingCard}>
          <div className={styles.landingHeader}>
            <span className={styles.landingTag}>🔥 MargDarshak Roast & Refine</span>
            <h2 className={styles.landingTitle}>
              Your resume asked for a review.<br />
              <span className={styles.accentText}>It got a roast.</span>
            </h2>
            <p className={styles.landingSub}>
              SAVAGE. BRUTAL. WITTY. CONSTRUCTIVE.<br />
              Turn harsh career criticism into actionable improvements.
            </p>
          </div>

          {currentFile ? (
            <div className={styles.readyFileCard}>
              <div className={styles.fileIcon}>{getFileIcon(currentFile.name)}</div>
              <div className={styles.fileDetails}>
                <span className={styles.fileName}>{currentFile.name || 'Resume'}</span>
                <span className={styles.fileSize}>
                  {currentFile.size ? `${(currentFile.size / 1024).toFixed(1)} KB` : 'Ready'}
                </span>
              </div>
              <div className={styles.readyFileActions}>
                {/* Hidden native input for swapping the file */}
                <input
                  ref={changeFileRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.webp"
                  style={{ display: 'none' }}
                  onChange={handleChangeFileInput}
                />
                <button
                  type="button"
                  className={styles.changeFileBtn}
                  onClick={() => changeFileRef.current?.click()}
                  title="Upload a different resume"
                >
                  ↕ Change
                </button>
                <button type="button" className={styles.mainRoastBtn} onClick={handleRoast}>
                  🔥 Roast My Resume
                </button>
              </div>
            </div>
          ) : (
            <div
              {...getRootProps()}
              className={`${styles.dropzone} ${isDragActive ? styles.dropActive : ''}`}
            >
              <input {...getInputProps()} />
              <div className={styles.dropIcon}>📂</div>
              <p>Drag &amp; drop your resume here, or click to browse</p>
              <span className={styles.dropHint}>PDF, JPG, JPEG, PNG, WEBP — up to 5 MB</span>
            </div>
          )}

          {error && (
            <div className={styles.errorBanner}>
              <span>⚠️ {error}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ─── LOADING ──────────────────────────────────────────────
  if (loadingRoast) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingCard}>
          <div className={styles.flameSpinner}>🔥</div>
          <h3 className={styles.loadingTitle}>{LOADING_MESSAGES[loadingStep]}</h3>
          <div className={styles.loadingBarBg}>
            <div
              className={styles.loadingBarFill}
              style={{ width: `${((loadingStep + 1) / LOADING_MESSAGES.length) * 100}%` }}
            />
          </div>
        </div>
      </div>
    )
  }

  // ─── RESULTS ──────────────────────────────────────────────
  const scores = roastData.section_scores || {}
  const overall10 = toTen(roastData.overall_score || 0)
  const color = scoreColor(overall10)
  const verdict = scoreVerdict(overall10)
  const issues = roastData.issues || []
  const sectionRoasts = roastData.section_roasts || {}
  const topFixes = roastData.top_fixes || []

  // Group issues by section for per-section display
  const bySection = {}
  issues.forEach(issue => {
    const sec = issue.section || 'General'
    if (!bySection[sec]) bySection[sec] = []
    bySection[sec].push(issue)
  })

  return (
    <div className={styles.container}>

      {/* ── Back button ── */}
      <div className={styles.resultsTopBar}>
        <button
          type="button"
          className={styles.backBtn}
          onClick={() => { setRoastData(null); setError(null) }}
        >
          ← Roast This Resume Again
        </button>
        {/* hidden input for swapping from results page too */}
        <input
          ref={changeFileRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          style={{ display: 'none' }}
          onChange={handleChangeFileInput}
        />
        <button
          type="button"
          className={styles.swapResumeBtn}
          onClick={() => changeFileRef.current?.click()}
        >
          📂 Roast a Different Resume
        </button>
      </div>

      {/* ── Headline Roast Banner ── */}
      <div className={styles.headlineBanner}>
        <span className={styles.flameGiant}>🔥</span>
        <div>
          <p className={styles.headlineQuoteText}>"{roastData.headline_roast}"</p>
          <p className={styles.headlineSub}>{roastData.summary}</p>
        </div>
      </div>

      {/* ── Score Card ── */}
      <div className={styles.scoreResultCard}>
        <div className={styles.scoreResultHeader}>
          <span className={styles.scoreResultLabel}>Resume Score</span>
        </div>
        <div className={styles.scoreBigRow}>
          <div className={styles.scoreBigCircle} style={{ borderColor: color }}>
            <span className={styles.scoreBigNum} style={{ color }}>{overall10}</span>
            <span className={styles.scoreBigDen}>/10</span>
          </div>
          <div className={styles.scoreVerdictBlock}>
            <span className={styles.scoreVerdictText} style={{ color }}>{verdict}</span>
            <p className={styles.scoreVerdictSub}>
              Based on structure, clarity, impact, ATS fit, skills, and conciseness.
            </p>
          </div>
        </div>

        {/* Sub-dimension bars */}
        <div className={styles.scoreDimsGrid}>
          {Object.entries(SECTION_SCORE_LABELS).map(([key, label]) => {
            const raw = scores[key] ?? 0
            const val10 = toTen(raw)
            const col = scoreColor(val10)
            const icon = SECTION_ICONS[key] || '📊'
            return (
              <div key={key} className={styles.scoreDimItem}>
                <div className={styles.scoreDimTop}>
                  <span className={styles.scoreDimLabel}>{icon} {label}</span>
                  <span className={styles.scoreDimVal} style={{ color: col }}>{val10}/10</span>
                </div>
                <div className={styles.scoreDimBarBg}>
                  <div
                    className={styles.scoreDimBarFill}
                    style={{ width: `${raw}%`, background: col }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Per-Section Roast ── */}
      {Object.keys(bySection).length > 0 && (
        <div className={styles.sectionRoastsCard}>
          <h3 className={styles.sectionRoastsTitle}>🔥 Section-by-Section Roast</h3>
          <p className={styles.sectionRoastsSub}>Every section of your resume, brutally reviewed.</p>
          <div className={styles.sectionRoastsList}>
            {Object.entries(bySection).map(([sec, secIssues]) => {
              const customRoast = sectionRoasts[sec.toLowerCase()]
              return (
                <div key={sec} className={styles.sectionRoastBlock}>
                  <div className={styles.sectionRoastHeader}>
                    <span className={styles.sectionRoastName}>{sec}</span>
                    <span className={styles.sectionIssueBadge}>
                      {secIssues.length} issue{secIssues.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  {customRoast && (
                    <div className={styles.sectionCustomRoast}>
                      💀 {customRoast}
                    </div>
                  )}
                  <div className={styles.sectionIssueList}>
                    {secIssues.map((issue, idx) => (
                      <div key={idx} className={styles.issueRow}>
                        <div className={styles.issueRowTop}>
                          <span className={
                            issue.severity === 'high' ? styles.sevHigh
                            : issue.severity === 'medium' ? styles.sevMed
                            : styles.sevLow
                          }>
                            {issue.severity.toUpperCase()}
                          </span>
                          <span className={styles.issueCat}>{issue.category.replace(/_/g, ' ')}</span>
                        </div>
                        <p className={styles.issueRoastText}>🔥 {issue.roast}</p>
                        {issue.evidence && (
                          <div className={styles.issueEvidence}>
                            <span className={styles.evidenceLabel}>Found:</span> "{issue.evidence}"
                          </div>
                        )}
                        <div className={styles.issueFix}>
                          <span className={styles.issueFixLabel}>Fix →</span> {issue.suggestion}
                        </div>
                        {issue.rewrite_example && (
                          <div className={styles.issueRewrite}>
                            <span className={styles.rewriteTag}>✅ Example</span>
                            <span className={styles.rewriteText}>{issue.rewrite_example}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Top 3 Quick Fixes ── */}
      {topFixes.length > 0 && (
        <div className={styles.topFixesCard}>
          <h3 className={styles.topFixesTitle}>🛠️ Top Fixes to Implement Now</h3>
          <ol className={styles.topFixesList}>
            {topFixes.map((fix, i) => (
              <li key={i} className={styles.topFixItem}>
                <span className={styles.topFixNum}>{i + 1}</span>
                <span>{fix}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

    </div>
  )
}

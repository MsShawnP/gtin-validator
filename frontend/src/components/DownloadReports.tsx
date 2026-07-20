import { useState } from 'react'
import * as api from '../api'
import styles from './DownloadReports.module.css'

// Lead capture is routed through the main site (single MailerLite key + Lead
// Source field there). Only the email address and summary metrics are ever
// sent — never the uploaded file or any row-level data.
const SUBSCRIBE_ENDPOINT = 'https://lailarallc.com/api/tool-subscribe'
const UNLOCK_KEY = 'gtin_reports_unlocked'

interface Props {
  token: string
  companyName: string
  onCompanyNameChange: (name: string) => void
  grade: string
  score: number
  criticalCount: number
}

function DownloadButton({
  label,
  onClick,
}: {
  label: string
  onClick: () => Promise<void>
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  return (
    <>
      <button
        className="btn btn-primary btn-full"
        disabled={loading}
        onClick={async () => {
          setError('')
          setLoading(true)
          try {
            await onClick()
          } catch (e) {
            setError(
              e instanceof Error && e.name === 'AbortError'
                ? 'Request timed out. Try again in a moment.'
                : 'Download failed. Please try again.',
            )
          } finally {
            setLoading(false)
          }
        }}
      >
        {loading ? <span className="spinner" /> : null}
        {label}
      </button>
      {error && <p className="text-error" style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>{error}</p>}
    </>
  )
}

export default function DownloadReports({
  token,
  companyName,
  onCompanyNameChange,
  grade,
  score,
  criticalCount,
}: Props) {
  const [unlocked, setUnlocked] = useState(() => {
    try {
      return sessionStorage.getItem(UNLOCK_KEY) === '1'
    } catch {
      return false
    }
  })
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function unlock() {
    try {
      sessionStorage.setItem(UNLOCK_KEY, '1')
    } catch {
      /* sessionStorage unavailable — still unlock for this session */
    }
    setUnlocked(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    // Send only the email + summary metrics. The uploaded file is not part of this request.
    try {
      await fetch(SUBSCRIBE_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          source: 'gtin-validator',
          grade,
          score,
          criticalCount,
        }),
      })
    } catch {
      /* never hold the downloads hostage to a failed network call */
    }
    unlock()
  }

  return (
    <section className={styles.section}>
      <h3>Download Validation Reports</h3>

      {!unlocked ? (
        <form className={styles.gate} onSubmit={handleSubmit}>
          <h4>Where should I send these?</h4>
          <p>
            Enter your email to unlock all three reports. Your email is all I
            receive &mdash; it is never matched to your file or your results.
          </p>
          <div className={styles.gateRow}>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Work email"
              aria-label="Work email"
            />
            <button
              className="btn btn-primary"
              type="submit"
              disabled={submitting}
            >
              {submitting ? <span className="spinner" /> : null}
              Unlock my reports
            </button>
          </div>
          <p className={styles.finePrint}>
            You&rsquo;ll also get occasional writing on deductions and retailer
            data. Unsubscribe anytime.
          </p>
        </form>
      ) : (
        <>
          <div className={styles.companyInput}>
            <label htmlFor="company-name">Company name (optional)</label>
            <input
              id="company-name"
              type="text"
              value={companyName}
              onChange={(e) => onCompanyNameChange(e.target.value)}
              placeholder="e.g., Cedar Hollow Provisions"
            />
          </div>

          <div className={styles.grid}>
            <div className={styles.card}>
              <h4>Corrected GTINs</h4>
              <p>
                Clean CSV with corrected check digits and formatting fixes
                applied. Paste directly into your product master or retailer
                portal.
              </p>
              <DownloadButton
                label="Download Corrected CSV"
                onClick={() => api.downloadCorrectedCsv(token, companyName)}
              />
            </div>

            <div className={styles.card}>
              <h4>CSV Report — Raw Data</h4>
              <p>
                Row-by-row validation results with issue codes, recommendations,
                and retailer impact. Best for Excel analysis.
              </p>
              <DownloadButton
                label="Download CSV Report"
                onClick={() => api.downloadCsvReport(token, companyName)}
              />
            </div>

            <div className={styles.card}>
              <h4>PDF Report — Full Diagnostic</h4>
              <p>
                Branded report with readiness score, retailer checklists, and
                cost-of-inaction estimates. Hand to your COO or broker.
              </p>
              <DownloadButton
                label="Download PDF Report"
                onClick={() => api.downloadPdfReport(token, companyName)}
              />
            </div>
          </div>
        </>
      )}
    </section>
  )
}

import { useState } from 'react'
import * as api from '../api'
import styles from './DownloadReports.module.css'

interface Props {
  token: string
  companyName: string
  onCompanyNameChange: (name: string) => void
}

function DownloadButton({
  label,
  onClick,
}: {
  label: string
  onClick: () => Promise<void>
}) {
  const [loading, setLoading] = useState(false)
  return (
    <button
      className="btn btn-primary btn-full"
      disabled={loading}
      onClick={async () => {
        setLoading(true)
        try {
          await onClick()
        } finally {
          setLoading(false)
        }
      }}
    >
      {loading ? <span className="spinner" /> : null}
      {label}
    </button>
  )
}

export default function DownloadReports({
  token,
  companyName,
  onCompanyNameChange,
}: Props) {
  return (
    <section className={styles.section}>
      <h3>Download Validation Reports</h3>

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
            Clean CSV with corrected check digits and formatting fixes applied.
            Paste directly into your product master or retailer portal.
          </p>
          <DownloadButton
            label="Download Corrected GTINs"
            onClick={() => api.downloadCorrectedCsv(token, companyName)}
          />
        </div>

        <div className={styles.card}>
          <h4>CSV Report — Raw Data</h4>
          <p>
            Row-by-row validation results with issue codes, recommendations, and
            retailer impact. Best for Excel analysis.
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
    </section>
  )
}

import type { BatchSummary } from '../types'
import styles from './SummaryStats.module.css'

export default function SummaryStats({ summary }: { summary: BatchSummary }) {
  return (
    <div className={styles.row}>
      <div className={styles.card}>
        <div className={styles.number}>{summary.total_gtins}</div>
        <div className={styles.label}>Total GTINs</div>
      </div>
      <div className={`${styles.card} ${styles.critical}`}>
        <div className={styles.number}>{summary.critical_issues}</div>
        <div className={styles.label}>Critical Issues</div>
      </div>
      <div className={`${styles.card} ${styles.warning}`}>
        <div className={styles.number}>{summary.warnings}</div>
        <div className={styles.label}>Warnings</div>
      </div>
      <div className={`${styles.card} ${styles.clean}`}>
        <div className={styles.number}>{summary.clean}</div>
        <div className={styles.label}>Clean</div>
      </div>
    </div>
  )
}

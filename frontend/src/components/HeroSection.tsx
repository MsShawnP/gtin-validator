import styles from './HeroSection.module.css'

export default function HeroSection() {
  return (
    <section className={styles.hero}>
      <h2 className={styles.title}>Validate your product GTINs in seconds</h2>
      <p className={styles.subtitle}>
        Find data quality issues before retailers do. Check your GTINs against
        GS1 format standards and retailer requirement rules &mdash; get a
        readiness score, prioritized fix plan, and branded PDF report.
      </p>
      <div className={styles.cards}>
        <div className={styles.card}>
          <strong>Why it pays</strong>
          <p>
            A bad GTIN doesn&apos;t fail loudly — it becomes a rejected item form,
            a delayed launch, or a chargeback weeks later. Checks run against GS1
            format standards, retailer submission rules (Walmart, Costco, UNFI),
            packaging hierarchy, and duplicates — before a retailer finds them.
          </p>
        </div>
        <div className={styles.card}>
          <strong>What this does NOT do</strong>
          <p>
            This does not look up GTINs in retailer databases or verify product
            assignments. It validates your data format and structure &mdash; a
            pre-flight check before you submit.
          </p>
        </div>
        <div className={styles.card}>
          <strong>What you'll need</strong>
          <p>
            A list of GTINs &mdash; upload a CSV or Excel file, or paste them
            directly. No account needed. Your file is never stored &mdash;
            results are held in memory for 30 minutes, then discarded.
          </p>
        </div>
      </div>
    </section>
  )
}

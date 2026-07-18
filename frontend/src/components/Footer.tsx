import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p>
        Built for specialty food brands. Not affiliated with GS1, Walmart, or
        any retailer. Built by{' '}
        <a href="https://lailarallc.com" target="_blank" rel="noopener noreferrer">
          Lailara LLC
        </a>{' '}
        &mdash; data hygiene and analytics for specialty food brands scaling
        into national retail.
      </p>
    </footer>
  )
}

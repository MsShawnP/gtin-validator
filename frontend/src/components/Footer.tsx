import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p>
        Built for specialty food brands. Not affiliated with GS1, Walmart, or
        any retailer.
      </p>
      <p>
        For a comprehensive Product Data Health Audit,{' '}
        <a href="mailto:msshawnp@gmail.com">get in touch</a>.
      </p>
    </footer>
  )
}

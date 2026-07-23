import styles from './ResultsCTA.module.css'

interface Props {
  score: number
  grade: string
  total: number
  criticalCount: number
  warningCount: number
  companyName: string
}

export default function ResultsCTA({
  score,
  grade,
  total,
  criticalCount,
  warningCount,
  companyName,
}: Props) {
  const brand = companyName.trim() || 'my brand'
  const subject = `GTIN validation results — ${brand}`
  // Prefilled summary only — the user attaches their own file from their own
  // mail client. Nothing is uploaded anywhere.
  const body =
    'Hi Shawn,\r\n\r\n' +
    'I ran my GTINs through your validator and got:\r\n\r\n' +
    `Score: ${score} (Grade ${grade})\r\n` +
    ` Total GTINs: ${total}\r\n` +
    ` Critical issues: ${criticalCount}\r\n` +
    ` Warnings: ${warningCount}\r\n\r\n` +
    'My file is attached. What are these actually going to cost me?\r\n\r\n' +
    'Thanks,\r\n'
  const mailto = `mailto:shawn@lailarallc.com?subject=${encodeURIComponent(
    subject,
  )}&body=${encodeURIComponent(body)}`

  if (criticalCount > 0) {
    return (
      <section className={`${styles.cta} ${styles.critical}`}>
        <h2>{criticalCount} of your GTINs will be rejected.</h2>
        <p>
          Critical issues are the ones retailers bounce at item setup. Send me
          your file and I&rsquo;ll tell you which ones will actually cost you
          &mdash; the rejections, the chargebacks, and what they add up to.
          You&rsquo;ll get it back in writing. No call.
        </p>
        <a className="btn btn-primary" href={mailto}>
          Send my file to Shawn for a free read
        </a>
        <p className={styles.helper}>
          Opens your email app with the summary filled in — attach your file and
          send.
        </p>
        <a
          className={styles.secondary}
          href="https://lailarallc.com/services"
          target="_blank"
          rel="noopener noreferrer"
        >
          See how the full audit works →
        </a>
      </section>
    )
  }

  // Clean-case handoff: same prefilled-mailto mechanism as the issues branch,
  // adapted to a clean result. Still only a summary — nothing uploaded.
  const cleanBody =
    'Hi Shawn,\r\n\r\n' +
    'I ran my GTINs through your validator and they came back clean:\r\n\r\n' +
    `Score: ${score} (Grade ${grade})\r\n` +
    ` Total GTINs: ${total}\r\n\r\n` +
    'My product master is attached — I’d like the same check across the full file.\r\n\r\n' +
    'Thanks,\r\n'
  const cleanMailto = `mailto:shawn@lailarallc.com?subject=${encodeURIComponent(
    subject,
  )}&body=${encodeURIComponent(cleanBody)}`

  return (
    <section className={`${styles.cta} ${styles.clean}`}>
      <h2>Your GTINs are clean.</h2>
      <p>
        Clean GTINs put you ahead of most brands at item setup &mdash; but GTINs
        are one field. The same check across your full product master
        (dimensions, case packs, GDSN records) is where the expensive misses
        hide, and they never show up in a GTIN scan. Send it over and
        I&rsquo;ll write back with what I find. No call.
      </p>
      <a className="btn btn-primary" href={cleanMailto}>
        Send me your product master for a free read
      </a>
      <p className={styles.helper}>
        Opens your email app with a note filled in — attach your file and send.
      </p>
      <a
        className={styles.secondary}
        href="https://lailarallc.com/services"
        target="_blank"
        rel="noopener noreferrer"
      >
        See how the full audit works →
      </a>
    </section>
  )
}

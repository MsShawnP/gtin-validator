import type { ScoreResult } from '../types'
import styles from './ScoreCard.module.css'

function scoreColor(score: number): string {
  if (score >= 75) return '#158f75'
  if (score >= 50) return '#ee8a2a'
  return '#cc100a'
}

export default function ScoreCard({ score }: { score: ScoreResult }) {
  return (
    <div className={styles.card}>
      <div className={styles.number} style={{ color: scoreColor(score.score) }}>
        {score.score}
      </div>
      <div className={styles.grade}>Grade: {score.grade}</div>
      <div className={styles.interp}>{score.interpretation}</div>
    </div>
  )
}

import { EMOTION_COLOR, signed } from '../../lib/format'
import { Badge } from '../ui'

export function EmotionBadge({ emotion }) {
  return (
    <span className="badge badge-emotion" style={{ background: EMOTION_COLOR[emotion] || 'var(--surface-2)' }}>
      {emotion}
    </span>
  )
}

export function SampleBadge() {
  return <Badge tone="sample">Sample</Badge>
}

export function ScorePill({ score }) {
  if (score == null) return <span className="muted">—</span>
  const cls = score >= 80 ? 'score-hi' : score >= 60 ? 'score-mid' : 'score-lo'
  return <span className={`score-pill ${cls}`}>{Math.round(score)}</span>
}

export function SentimentValue({ value }) {
  if (value == null) return <span className="muted">—</span>
  const cls = value >= 0.15 ? 'pos' : value <= -0.15 ? 'neg' : 'zero'
  return <span className={`mono ${cls}`}>{signed(value)}</span>
}

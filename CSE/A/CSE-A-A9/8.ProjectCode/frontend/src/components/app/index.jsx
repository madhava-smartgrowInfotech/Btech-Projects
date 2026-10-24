// Project-level building blocks shared by the screens.
import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react'
import { fmtScore } from '../../lib/format'
import { Badge, ErrorState, PageSkeleton } from '../ui'

const CALLOUT_ICON = { info: Info, success: CheckCircle2, warn: AlertTriangle, error: XCircle }

export function Callout({ tone = 'info', title, children, role }) {
  const Icon = CALLOUT_ICON[tone] || Info
  return (
    <div className={`callout ${tone}`} role={role || (tone === 'error' ? 'alert' : 'note')}>
      <Icon size={20} aria-hidden="true" />
      <div>
        {title && <strong>{title}</strong>}
        <div>{children}</div>
      </div>
    </div>
  )
}

/** Renders a useAsync() result: skeleton while loading, an error state with retry, then the data. */
export function Load({ state, children, skeleton, title = 'Could not load this screen' }) {
  if (state.loading && !state.data) return skeleton || <PageSkeleton />
  if (state.error && !state.data) return <ErrorState title={title} error={state.error} onRetry={state.reload} />
  if (!state.data) return null
  return children(state.data)
}

export const scoreTone = (score, threshold = 0.5) => (score >= threshold ? 'rose' : score >= 0.3 ? 'peach' : 'mint')
export const scoreColor = (score, threshold = 0.5) => `var(--${scoreTone(score, threshold)})`

export function ScoreBadge({ score, threshold }) {
  return (
    <Badge tone={scoreTone(score, threshold)} dot>
      {fmtScore(score)} fake
    </Badge>
  )
}

/** Probability bar + number, used in table rows. */
export function ScoreCell({ score, threshold }) {
  return (
    <span className="prob-cell">
      <span className="bar-track" aria-hidden="true">
        <span className="bar-fill" style={{ display: 'block', width: `${Math.max(2, score * 100)}%`, background: scoreColor(score, threshold) }} />
      </span>
      <b className="num">{fmtScore(score)}</b>
    </span>
  )
}

const STATUS = {
  pending: { tone: 'peach', label: 'Needs review' },
  confirmed: { tone: 'rose', label: 'Confirmed fake' },
  dismissed: { tone: 'mint', label: 'Dismissed' },
  clear: { tone: 'neutral', label: 'Not flagged' },
}
export function StatusBadge({ status }) {
  const s = STATUS[status] || STATUS.clear
  return <Badge tone={s.tone}>{s.label}</Badge>
}

/** Semi-circular probability gauge. */
export function Gauge({ value, threshold = 0.5, label = 'Fake probability' }) {
  const v = Math.max(0, Math.min(100, (value ?? 0) * 100))
  const arc = 'M 20 100 A 80 80 0 0 1 180 100'
  return (
    <div className="gauge" role="img" aria-label={`${label}: ${v.toFixed(0)} percent`}>
      <svg viewBox="0 0 200 118" aria-hidden="true">
        <path d={arc} className="gauge-track" />
        <motion.path
          d={arc}
          className="gauge-arc"
          style={{ stroke: scoreColor(value, threshold) }}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: v / 100 }}
          transition={{ type: 'spring', stiffness: 60, damping: 16 }}
        />
        <text x="100" y="92" textAnchor="middle" className="gauge-num">
          {v.toFixed(0)}%
        </text>
        <text x="100" y="112" textAnchor="middle" className="gauge-label">
          {label}
        </text>
      </svg>
    </div>
  )
}

/** Signed horizontal bars: positive pushes towards "fake", negative towards "genuine". */
export function ContribBars({ items, max }) {
  const m = max || Math.max(...items.map((i) => Math.abs(i.contribution)), 0.001)
  return (
    <ul className="driver-list">
      {items.map((i) => {
        const pos = i.contribution >= 0
        return (
          <li key={i.feature}>
            <div className="driver-row">
              <span>{i.label}</span>
              <span className="tiny num">
                {pos ? '+' : '−'}
                {Math.abs(i.contribution).toFixed(2)}
              </span>
            </div>
            <div className="bar-track" title={i.group}>
              <div className="bar-fill" style={{ width: `${(Math.abs(i.contribution) / m) * 100}%`, background: pos ? 'var(--rose)' : 'var(--mint)' }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

import { Badge, ProgressBar } from '../ui'
import { pct, SAFETY_LABEL, SAFETY_TONE } from '../../lib/format'

const SEVERITY_TONE = { low: 'pass', moderate: 'upcoming', high: 'blocked', emergency: 'blocked' }

export function SafetyBadge({ flag }) {
  const f = flag || 'routine'
  return <Badge tone={SAFETY_TONE[f] || 'expired'}>{SAFETY_LABEL[f] || f}</Badge>
}

export function Relevance({ value }) {
  return (
    <div className="rel" title="Match relevance - similarity to the knowledge-base record, not a medical probability">
      <ProgressBar value={value || 0} max={1} label="Match relevance" />
      <strong>{pct(value)}</strong>
    </div>
  )
}

export function EvidenceCard({ item, rank }) {
  return (
    <article className={`ev-card ${rank === 1 ? 'top' : ''}`}>
      <div className="ev-head">
        <div>
          <div className="ev-rank">{rank === 1 ? 'Top match' : `Match ${rank}`}</div>
          <h3 className="ev-title">{item.disease}</h3>
        </div>
        <div className="row" style={{ '--gap': '10px' }}>
          {item.severity && <Badge tone={SEVERITY_TONE[item.severity] || 'expired'}>Severity: {item.severity}</Badge>}
          <Relevance value={item.relevance} />
        </div>
      </div>
      {item.symptoms && (
        <p className="ev-sec">
          <b>Typical symptoms</b>
          {item.symptoms}
        </p>
      )}
      {item.description && (
        <p className="ev-sec">
          <b>About</b>
          {item.description}
        </p>
      )}
      {item.guidance && (
        <p className="ev-sec">
          <b>Guidance</b>
          {item.guidance}
        </p>
      )}
      {item.red_flags && (
        <p className="ev-sec ev-red">
          <b>Seek urgent care if</b>
          {item.red_flags}
        </p>
      )}
    </article>
  )
}

export function EvidenceList({ items = [] }) {
  if (!items.length) return null
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <span className="eyebrow">Possible conditions from matching medical information</span>
      <div className="ev-list">
        {items.map((e, i) => (
          <EvidenceCard key={e.record_id || i} item={e} rank={i + 1} />
        ))}
      </div>
    </div>
  )
}

export const DISCLAIMER_TEXT = 'Preliminary information only - not a medical diagnosis. Consult a qualified healthcare professional; in an emergency seek immediate care.'

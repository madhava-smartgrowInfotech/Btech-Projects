import { PRIORITY_NAME } from '../../lib/format'

export function PriorityBlock({ p, size }) {
  return (
    <span className={`prio ${size === 'lg' ? 'lg' : ''}`} data-p={p} role="img" aria-label={`Priority ${p}, ${PRIORITY_NAME[p]}`}>
      {p}
    </span>
  )
}

/** SHAP attribution as hard-edged diverging bars, strongest first. */
export function ShapBars({ items }) {
  const max = Math.max(...items.map((i) => Math.abs(i.impact)), 0.0001)
  return (
    <div className="stack" style={{ '--gap': '12px' }}>
      <ul className="shap-list" aria-label="Factors that drove the priority, strongest first">
        {items.map((s) => {
          const w = Math.max(2, (Math.abs(s.impact) / max) * 50)
          const up = s.impact > 0
          return (
            <li className="shap-row" key={s.feature}>
              <div className="shap-label">
                <strong>{s.label}</strong>
                <span>{s.value}</span>
              </div>
              <div className="shap-track" title={`${s.label}: ${s.impact > 0 ? '+' : ''}${s.impact.toFixed(2)} ${s.direction}`}>
                <span className={`shap-bar ${up ? 'up' : 'down'}`} style={{ width: `${w}%` }} />
              </div>
              <span className="shap-val">
                {up ? '+' : ''}
                {s.impact.toFixed(2)}
              </span>
            </li>
          )
        })}
      </ul>
      <div className="shap-axis" aria-hidden="true">
        <span>← lowers urgency</span>
        <span>raises urgency →</span>
      </div>
    </div>
  )
}

export function FindingChips({ items, empty = 'None found in the report.' }) {
  if (!items?.length) return <p className="small muted">{empty}</p>
  return (
    <div className="chip-list">
      {items.map((i) => (
        <span className="chip" key={i.flag}>
          {i.label}
          <small>p.{i.page}</small>
        </span>
      ))}
    </div>
  )
}

export function LabChips({ labs }) {
  if (!labs?.length) return <p className="small muted">No lab values found in the report.</p>
  return (
    <div className="chip-list">
      {labs.map((l, i) => (
        <span className={`chip ${l.abnormal ? 'abn' : ''}`} key={`${l.name}-${i}`} title={`Reference ${l.reference} ${l.unit}`}>
          {l.name} {l.value} {l.unit}
          <small>p.{l.page}</small>
        </span>
      ))}
    </div>
  )
}

import { Check, X } from 'lucide-react'
import { CursorHighlight, CountUp } from '../motion'

export function Card({ title, actions, tone, flat, hot, className = '', children, as, ...rest }) {
  const cls = ['card', tone && `card-${tone}`, flat && 'card-flat', className].filter(Boolean).join(' ')
  const body = (
    <>
      {(title || actions) && (
        <div className="card-head">
          {title && <h2 className="card-title">{title}</h2>}
          {actions && <div className="row">{actions}</div>}
        </div>
      )}
      {children}
    </>
  )
  if (hot) {
    return (
      <CursorHighlight className={cls} as={as || 'div'} {...rest}>
        {body}
      </CursorHighlight>
    )
  }
  const Tag = as || 'section'
  return (
    <Tag className={cls} {...rest}>
      {body}
    </Tag>
  )
}

/** Inline-SVG sparkline: thick flat line + square markers, no smoothing, no gradient fill. */
export function Sparkline({ data = [], color = 'var(--fg)', width = 120, height = 34, label }) {
  if (!data.length) return null
  const max = Math.max(...data, 1)
  const step = data.length > 1 ? (width - 6) / (data.length - 1) : 0
  const pts = data.map((v, i) => [3 + i * step, height - 3 - (v / max) * (height - 6)])
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ')
  const last = pts[pts.length - 1]
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label || 'trend'}>
      <path d={d} fill="none" stroke={color} strokeWidth="3" strokeLinejoin="miter" />
      <rect x={last[0] - 4} y={last[1] - 4} width="8" height="8" fill="var(--lime)" stroke="var(--ink)" strokeWidth="2" />
    </svg>
  )
}

export function StatCard({ label, value, decimals = 0, delta, deltaTone, spark, tone, icon: Icon, hint }) {
  const numeric = typeof value === 'number'
  return (
    <Card tone={tone} hot className="stat">
      <div className="row-between">
        <span className="stat-label">{label}</span>
        {Icon && <Icon size={20} aria-hidden="true" />}
      </div>
      <span className={`stat-value ${!numeric && String(value).length > 9 ? 'stat-value-sm' : ''}`}>{numeric ? <CountUp value={value} decimals={decimals} /> : value}</span>
      <div className="stat-foot">
        <div className="stack" style={{ '--gap': '4px' }}>
          {delta !== undefined && delta !== null && (
            <span className="delta" style={deltaTone ? { background: deltaTone, color: 'var(--ink)', borderColor: 'var(--ink)' } : undefined}>
              {delta}
            </span>
          )}
          {hint && <span className="tiny muted">{hint}</span>}
        </div>
        {spark && spark.length > 1 && <Sparkline data={spark} label={`${label} trend`} />}
      </div>
    </Card>
  )
}

export function Badge({ tone, children, dot }) {
  return (
    <span className={`badge ${tone ? `badge-${tone}` : ''}`}>
      {dot && <span className="badge-dot" aria-hidden="true" />}
      {children}
    </span>
  )
}

export function KeyValueList({ items }) {
  return (
    <dl className="kv">
      {items
        .filter((i) => i && i.value !== undefined)
        .map((i) => (
          <div key={i.label} style={{ display: 'contents' }}>
            <dt>{i.label}</dt>
            <dd>{i.value === null || i.value === '' ? '—' : i.value}</dd>
          </div>
        ))}
    </dl>
  )
}

/** items: [{title, meta, body, tone: 'ok'|'bad'|undefined, icon}] */
export function Timeline({ items }) {
  return (
    <ol className="timeline">
      {items.map((it, i) => {
        const Icon = it.icon || (it.tone === 'ok' ? Check : it.tone === 'bad' ? X : null)
        return (
          <li key={it.key || i}>
            <span className={`timeline-dot ${it.tone || ''}`} aria-hidden="true">
              {Icon && <Icon size={13} strokeWidth={3} />}
            </span>
            <div className="timeline-title">{it.title}</div>
            {it.meta && <div className="timeline-meta">{it.meta}</div>}
            {it.body && <div className="small" style={{ marginTop: 4 }}>{it.body}</div>}
          </li>
        )
      })}
    </ol>
  )
}

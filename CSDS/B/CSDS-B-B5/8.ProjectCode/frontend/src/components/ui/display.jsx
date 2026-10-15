import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { Suspense, lazy } from 'react'
import { CountUp } from '../motion'

// recharts is heavy: only fetched when a tile actually shows a sparkline
const Sparkline = lazy(() => import('./charts').then((m) => ({ default: m.Sparkline })))

export function Card({ title, eyebrow, action, children, className = '', bodyClass = 'p-4', id }) {
  return (
    <section id={id} className={`panel scan flex min-w-0 flex-col ${className}`}>
      {(title || action) && (
        <header className="relative z-[1] flex min-h-[44px] items-center justify-between gap-3 border-b border-line px-4 py-2.5">
          <div className="min-w-0">
            {eyebrow && <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">{eyebrow}</div>}
            <h2 className="flex items-center gap-2 truncate font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-muted">
              <span className="h-1.5 w-1.5 shrink-0 bg-ok" aria-hidden="true" />{title}
            </h2>
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div className={`relative z-[1] min-w-0 flex-1 ${bodyClass}`}>{children}</div>
    </section>
  )
}

export function StatusDot({ tone = 'ok', blink = true, ring = false, label, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <span className={`relative inline-block h-2 w-2 rounded-full ${blink ? 'dot-live' : ''} ${ring ? 'dot-ring' : ''}`}
        style={{ background: `var(--${tone})`, color: `var(--${tone})` }} aria-hidden="true" />
      {label && <span className="font-mono text-[11px] uppercase tracking-wider text-muted">{label}</span>}
    </span>
  )
}

export function StatCard({ label, value, format, sub, delta, deltaLabel = 'vs prev. month', spark, sparkKey, sparkLabel, tone = 'ok', icon: Icon, live = false }) {
  const up = delta !== null && delta !== undefined && delta >= 0
  return (
    <div className="panel scan flex h-full min-w-0 flex-col gap-2 p-4">
      <div className="relative z-[1] flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-2 truncate font-mono text-[10px] uppercase tracking-[0.14em] text-muted">
          {Icon && <Icon size={13} style={{ color: `var(--${tone})` }} aria-hidden="true" />}
          {label}
        </span>
        {live && <StatusDot tone={tone} />}
      </div>
      <div className="relative z-[1] flex items-end justify-between gap-2">
        <div className="min-w-0 truncate font-mono text-2xl font-semibold tracking-tight text-fg sm:text-[28px]">
          {typeof value === 'number' ? <CountUp value={value} format={format} /> : value}
        </div>
        {delta !== null && delta !== undefined && (
          <span title={deltaLabel} className={`mb-1 inline-flex shrink-0 items-center gap-0.5 font-mono text-[11px] ${up ? 'text-ok' : 'text-alert'}`}>
            {up ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}{Math.abs(delta * 100).toFixed(1)}%
            <span className="sr-only">{deltaLabel}</span>
          </span>
        )}
      </div>
      {sub && <div className="relative z-[1] truncate text-xs text-muted">{sub}</div>}
      {spark && (
        <div className="relative z-[1] -mx-1 mt-auto">
          <Suspense fallback={<div style={{ height: 36 }} />}><Sparkline data={spark} dataKey={sparkKey} tone={tone} label={sparkLabel} /></Suspense>
          {sparkLabel && <div className="px-1 font-mono text-[9px] uppercase tracking-wider text-dim">{sparkLabel}</div>}
        </div>
      )}
    </div>
  )
}

const BADGE = {
  neutral: 'border-line-strong text-muted', ok: 'border-ok/40 text-ok bg-ok/10', warn: 'border-warn/40 text-warn bg-warn/10',
  hot: 'border-hot/40 text-hot bg-hot/10', alert: 'border-alert/40 text-alert bg-alert/10', info: 'border-info/40 text-info bg-info/10',
  cyan: 'border-cyan/40 text-cyan bg-cyan/10',
}
export function Badge({ tone = 'neutral', children, dot = false, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-[4px] border px-1.5 py-[1px] font-mono text-[10px] uppercase tracking-wider ${BADGE[tone]} ${className}`}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />}
      {children}
    </span>
  )
}

// LED-segment score bar (0-1)
export function ScoreBar({ value, label, segments = 24, tone = 'ok', display }) {
  const lit = Math.max(value > 0 ? 1 : 0, Math.round(value * segments))
  const color = `var(--${tone})`
  return (
    <div>
      <div className="mb-1 flex justify-between gap-2 text-xs">
        <span className="truncate text-muted">{label}</span>
        <span className="font-mono tabular-nums" style={{ color }}>{display ?? value.toFixed(2)}</span>
      </div>
      <div className="flex h-2 gap-[2px]" role="meter" aria-valuemin={0} aria-valuemax={1} aria-valuenow={value} aria-label={label}>
        {Array.from({ length: segments }, (_, i) => (
          <span key={i} className="flex-1 rounded-[1px]" style={{ background: i < lit ? color : 'var(--line-strong)', opacity: i < lit ? 0.4 + 0.6 * ((i + 1) / lit) : 0.45 }} />
        ))}
      </div>
    </div>
  )
}

export function Timeline({ items }) {
  return (
    <ol className="relative ml-1.5 border-l border-line-strong">
      {items.map((it) => (
        <li key={it.id} id={it.anchor} className={`relative pb-4 pl-5 last:pb-0 ${it.className || ''}`}>
          <span className="absolute -left-[5px] top-1.5 h-[9px] w-[9px] rounded-full border-2 border-panel" style={{ background: `var(--${it.tone || 'dim'})` }} aria-hidden="true" />
          <div className="flex flex-wrap items-center gap-2">
            {it.time && <span className="font-mono text-[11px] text-dim">{it.time}</span>}
            <span className="text-sm font-medium text-fg">{it.title}</span>
            {it.meta}
          </div>
          {it.body && <div className="mt-1 text-xs leading-relaxed text-muted">{it.body}</div>}
        </li>
      ))}
    </ol>
  )
}

export function KeyValueList({ items, cols = 1 }) {
  return (
    <dl className={`grid gap-x-6 ${cols === 2 ? 'sm:grid-cols-2' : ''}`}>
      {items.map(([k, v]) => (
        <div key={k} className="flex items-baseline justify-between gap-4 border-b border-dashed border-line py-2 last:border-0">
          <dt className="text-xs text-muted">{k}</dt>
          <dd className="text-right font-mono text-[13px] tabular-nums text-fg">{v}</dd>
        </div>
      ))}
    </dl>
  )
}

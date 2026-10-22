import { useId } from 'react'
import { motion } from 'framer-motion'
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import { lift } from '../../lib/motion'
import { CountUp } from '../motion'

/** tint: lavender | mint | peach | sky ; hover lift on by default */
export function Card({ title, subtitle, actions, tint, hover = true, className = '', children, as = 'section', ...rest }) {
  const M = motion[as]
  return (
    <M className={`card ${tint ? `tint-${tint}` : ''} ${className}`} {...(hover ? { whileHover: lift.whileHover, transition: lift.transition } : {})} {...rest}>
      {(title || actions) && (
        <div className="card-head">
          <div style={{ minWidth: 0 }}>
            {title && <h2 style={{ fontSize: 17 }}>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {actions && <div className="row">{actions}</div>}
        </div>
      )}
      {children}
    </M>
  )
}

const TONES = { lavender: 'var(--lavender)', mint: 'var(--mint)', peach: 'var(--peach)', sky: 'var(--sky)', rose: 'var(--rose)' }

/** Tiny SVG sparkline - no chart library needed. */
export function Sparkline({ data = [], color = 'var(--lavender)', className = 'stat-spark' }) {
  const gid = useId().replace(/:/g, '')
  if (data.length < 2) return null
  const w = 100
  const h = 38
  const min = Math.min(...data)
  const max = Math.max(...data)
  const pts = data.map((v, i) => [(i / (data.length - 1)) * w, h - 4 - ((v - min) / (max - min || 1)) * (h - 8)])
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')
  return (
    <svg className={className} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" style={{ stopColor: color, stopOpacity: 0.55 }} />
          <stop offset="1" style={{ stopColor: color, stopOpacity: 0 }} />
        </linearGradient>
      </defs>
      <path d={`${line} L${w},${h} L0,${h} Z`} style={{ fill: `url(#${gid})` }} />
      <path d={line} style={{ fill: 'none', stroke: color, strokeWidth: 2.4, strokeLinecap: 'round', strokeLinejoin: 'round' }} vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

/**
 * KPI card. `value` numeric -> counts up with `format`; or pass `display` for a preformatted string.
 * delta: {value: number, label, good: 'up'|'down'}
 */
export function StatCard({ label, value, format, display, icon: Icon, tone = 'lavender', delta, spark, foot }) {
  let deltaEl = null
  if (delta && delta.value != null) {
    const dir = Math.abs(delta.value) < 1e-9 ? 'flat' : delta.value > 0 ? 'up' : 'down'
    const good = dir === 'flat' ? 'flat' : (dir === 'up') === ((delta.good || 'up') === 'up') ? 'up' : 'down'
    const Arrow = dir === 'flat' ? Minus : dir === 'up' ? ArrowUpRight : ArrowDownRight
    deltaEl = (
      <span className={`delta ${good}`}>
        <Arrow size={13} aria-hidden="true" />
        {delta.text}
      </span>
    )
  }
  return (
    <Card className="stat-card" hover>
      <div className="stat-top">
        <span className="stat-label">{label}</span>
        {Icon && (
          <span className="stat-ico" style={{ background: TONES[tone] }}>
            <Icon size={20} aria-hidden="true" />
          </span>
        )}
      </div>
      <div className="stat-value">{display != null ? display : <CountUp value={value} format={format} />}</div>
      <div className="stat-foot">
        <span style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', minWidth: 0 }}>
          {deltaEl}
          {delta?.label && <span>{delta.label}</span>}
          {foot && <span>{foot}</span>}
        </span>
        {spark && <Sparkline data={spark} color={TONES[tone]} />}
      </div>
    </Card>
  )
}

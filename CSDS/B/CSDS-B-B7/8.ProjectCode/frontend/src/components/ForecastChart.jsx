import { useState } from 'react'

/**
 * Line chart with an uncertainty band and an optional capacity line (plain SVG).
 * points: [{ label, mean, lower?, upper? }]
 */
export default function ForecastChart({ points, capacity, current, height = 180, unit = 'patients' }) {
  const [hover, setHover] = useState(null)
  const W = 560
  const H = height
  const pad = { l: 36, r: 12, t: 12, b: 24 }
  const n = points.length
  const values = points.flatMap((p) => [p.mean, p.upper ?? p.mean, p.lower ?? p.mean])
  if (capacity != null) values.push(capacity)
  if (current != null) values.push(current)
  const maxV = Math.max(...values) * 1.08 || 1
  const minV = Math.max(0, Math.min(...values) * 0.85)
  const x = (i) => pad.l + ((n <= 1 ? 0.5 : i / (n - 1)) * (W - pad.l - pad.r))
  const y = (v) => pad.t + (1 - (v - minV) / (maxV - minV || 1)) * (H - pad.t - pad.b)
  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.mean)}`).join(' ')
  const hasBand = points[0]?.upper != null
  const band = hasBand
    ? points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.upper)}`).join(' ') +
      ' ' +
      [...points].reverse().map((p, j) => `L${x(n - 1 - j)},${y(p.lower)}`).join(' ') +
      ' Z'
    : null
  const ticks = [minV, (minV + maxV) / 2, maxV]
  const over = capacity != null && points.some((p) => p.mean > capacity)

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" onMouseLeave={() => setHover(null)}>
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" />
            <text x={pad.l - 6} y={y(t) + 4} textAnchor="end" fontSize="10" fill="#94a3b8">
              {Math.round(t)}
            </text>
          </g>
        ))}
        {band && <path d={band} fill="#99f6e4" opacity="0.45" />}
        {capacity != null && (
          <g>
            <line x1={pad.l} x2={W - pad.r} y1={y(capacity)} y2={y(capacity)} stroke="#dc2626" strokeDasharray="5 4" strokeWidth="1.5" />
            <text x={W - pad.r} y={y(capacity) - 4} textAnchor="end" fontSize="10" fill="#dc2626">
              capacity {capacity}
            </text>
          </g>
        )}
        <path d={line} fill="none" stroke={over ? '#b91c1c' : '#0f766e'} strokeWidth="2.2" />
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={x(i)} cy={y(p.mean)} r={hover === i ? 4 : 2.5} fill={capacity != null && p.mean > capacity ? '#dc2626' : '#0f766e'} />
            <rect x={x(i) - (W - pad.l - pad.r) / n / 2} y={pad.t} width={(W - pad.l - pad.r) / n} height={H - pad.t - pad.b} fill="transparent" onMouseEnter={() => setHover(i)} />
          </g>
        ))}
        {points.map((p, i) =>
          i % Math.ceil(n / 7) === 0 || i === n - 1 ? (
            <text key={`l${i}`} x={x(i)} y={H - 6} textAnchor="middle" fontSize="10" fill="#64748b">
              {p.label}
            </text>
          ) : null,
        )}
      </svg>
      {hover != null && (
        <div className="absolute top-1 left-12 rounded-md bg-slate-900/90 text-white text-xs px-2 py-1 pointer-events-none">
          {points[hover].label}: <strong>{points[hover].mean}</strong> {unit}
          {hasBand && ` (90%: ${points[hover].lower}-${points[hover].upper})`}
        </div>
      )}
    </div>
  )
}

export const shortDate = (iso) => {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

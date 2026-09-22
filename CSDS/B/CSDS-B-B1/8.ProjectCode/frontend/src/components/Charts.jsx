import { useState } from 'react'
import { CHART } from './ui.jsx'

/** Single-series weekly sparkline with crosshair + tooltip (one small multiple). */
export function Sparkline({ title, weeks, counts, height = 64 }) {
  const [hover, setHover] = useState(null)
  const W = 240
  const H = height
  const pad = { l: 2, r: 8, t: 8, b: 4 }
  const max = Math.max(...counts, 1)
  const x = (i) => pad.l + (i * (W - pad.l - pad.r)) / Math.max(counts.length - 1, 1)
  const y = (v) => pad.t + (1 - v / max) * (H - pad.t - pad.b)
  const line = counts.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const area = `${line} L${x(counts.length - 1)},${H - pad.b} L${x(0)},${H - pad.b} Z`
  const last = counts.length - 1
  const total = counts.reduce((a, b) => a + b, 0)
  const i = hover ?? last

  function move(e) {
    const r = e.currentTarget.getBoundingClientRect()
    const px = ((e.clientX - r.left) / r.width) * W
    const idx = Math.round(((px - pad.l) / (W - pad.l - pad.r)) * (counts.length - 1))
    setHover(Math.min(Math.max(idx, 0), last))
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="flex items-baseline justify-between gap-2">
        <div className="truncate text-xs font-semibold text-slate-800" title={title}>
          {title}
        </div>
        <div className="text-xs tabular-nums text-slate-500">{total} total</div>
      </div>
      <div className="mt-0.5 text-[11px] text-slate-500">
        {hover === null ? 'Last 7 days' : `7 days from ${new Date(weeks[i]).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}`}:{' '}
        <b className="text-slate-800">{counts[i]}</b>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="mt-1 h-16 w-full touch-none"
        preserveAspectRatio="none"
        onPointerMove={move}
        onPointerLeave={() => setHover(null)}
        role="img"
        aria-label={`${title}: weekly complaints, ${counts.join(', ')}`}
      >
        <line x1={0} x2={W} y1={H - pad.b} y2={H - pad.b} stroke={CHART.grid} strokeWidth="1" vectorEffect="non-scaling-stroke" />
        <path d={area} fill={CHART.blue} opacity="0.1" />
        <path d={line} fill="none" stroke={CHART.blue} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
        {hover !== null && <line x1={x(i)} x2={x(i)} y1={pad.t - 4} y2={H - pad.b} stroke={CHART.axis} strokeWidth="1" vectorEffect="non-scaling-stroke" />}
      </svg>
      {/* end / hover dot drawn in HTML so it stays round when the SVG stretches */}
      <div className="relative -mt-16 h-16 pointer-events-none">
        <span
          className="absolute h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white"
          style={{ left: `${(x(i) / W) * 100}%`, top: `${(y(counts[i]) / H) * 100}%`, background: CHART.blue }}
        />
      </div>
    </div>
  )
}

/** Horizontal meter 0-100% (single hue), value printed beside it. */
export function Meter({ value, label }) {
  const w = value === null || value === undefined ? 0 : Math.max(value * 100, 1)
  return (
    <div className="flex items-center gap-2" title={label}>
      <div className="h-2.5 flex-1 rounded-r bg-[#cde2fb]">
        <div className="h-2.5 rounded-r" style={{ width: `${w}%`, background: CHART.blue }} />
      </div>
      <span className="w-12 text-right text-xs tabular-nums text-slate-700">{value === null || value === undefined ? '-' : `${Math.round(value * 100)}%`}</span>
    </div>
  )
}

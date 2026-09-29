import { ACTIVITY_COLORS, fmtDuration, label } from '../api.js'

// Horizontal activity timeline between `from` and `to` (Date objects).
export default function Timeline({ segments, from, to, ticks = 6 }) {
  const span = to - from
  const fmt = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return (
    <div>
      <div className="relative h-9 rounded-lg bg-slate-100 overflow-hidden">
        {segments.map((s, i) => {
          const a = Math.max(new Date(s.start) - from, 0)
          const b = Math.min(new Date(s.end) - from, span)
          if (b <= a) return null
          return (
            <div key={i} title={`${label(s.activity)} - ${fmtDuration((b - a) / 1000)}`}
              className="absolute top-0 bottom-0"
              style={{ left: `${(a / span) * 100}%`, width: `${Math.max(((b - a) / span) * 100, 0.3)}%`, background: ACTIVITY_COLORS[s.activity] || '#94a3b8' }} />
          )
        })}
      </div>
      <div className="flex justify-between text-[11px] text-slate-500 mt-1">
        {Array.from({ length: ticks + 1 }, (_, i) => <span key={i}>{fmt(new Date(from.getTime() + (span * i) / ticks))}</span>)}
      </div>
      <div className="flex flex-wrap gap-3 mt-2">
        {Object.entries(ACTIVITY_COLORS).map(([k, c]) => (
          <span key={k} className="flex items-center gap-1 text-xs text-slate-600 capitalize">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: c }} /> {label(k)}
          </span>
        ))}
      </div>
    </div>
  )
}

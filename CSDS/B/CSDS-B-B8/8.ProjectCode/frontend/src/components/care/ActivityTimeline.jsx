import { ACTIVITY_COLORS, activityColor, duration, humanize } from '../../lib/format'

// Horizontal activity timeline between `from` and `to` (Date objects).
export default function ActivityTimeline({ segments, from, to, ticks = 6 }) {
  const span = to - from
  const clock = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return (
    <div>
      <div className="atl-track" role="img" aria-label={`Activity timeline from ${clock(from)} to ${clock(to)}`}>
        {segments.map((s, i) => {
          const a = Math.max(new Date(s.start) - from, 0)
          const b = Math.min(new Date(s.end) - from, span)
          if (b <= a) return null
          return (
            <div
              key={`${s.start}-${i}`}
              className="atl-seg"
              title={`${humanize(s.activity)} - ${duration((b - a) / 1000)}`}
              style={{ left: `${(a / span) * 100}%`, width: `${Math.max(((b - a) / span) * 100, 0.3)}%`, background: activityColor(s.activity) }}
            />
          )
        })}
      </div>
      <div className="atl-ticks" aria-hidden="true">
        {Array.from({ length: ticks + 1 }, (_, i) => (
          <span key={i}>{clock(new Date(from.getTime() + (span * i) / ticks))}</span>
        ))}
      </div>
      <div className="legend" style={{ marginTop: 10 }}>
        {Object.entries(ACTIVITY_COLORS)
          .filter(([k]) => k !== 'away')
          .map(([k, c]) => (
            <span key={k} style={{ textTransform: 'capitalize' }}>
              <i style={{ background: c }} />
              {humanize(k)}
            </span>
          ))}
      </div>
    </div>
  )
}

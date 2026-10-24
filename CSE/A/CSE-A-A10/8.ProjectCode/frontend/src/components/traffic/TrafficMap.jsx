import { memo } from 'react'
import { SIGNAL_VAR, VEHICLE } from '../../format'

// Draws the junction grid from the server's map data. Coordinates are in simulator units with y pointing up,
// so every y is negated for SVG. Same layout as the original Plotly view (roads, vehicle squares, signal heads, labels).
function TrafficMap({ map, height = 'auto', compact = false, label = 'Road network map' }) {
  if (!map) return null
  const { bounds: b } = map
  const w = b.x1 - b.x0
  const h = b.y1 - b.y0
  const star = (cx, cy, r) => {
    const pts = []
    for (let i = 0; i < 10; i++) {
      const rr = i % 2 ? r * 0.45 : r
      const a = (Math.PI / 5) * i - Math.PI / 2
      pts.push(`${(cx + rr * Math.cos(a)).toFixed(2)},${(cy + rr * Math.sin(a)).toFixed(2)}`)
    }
    return pts.join(' ')
  }
  const amb = map.vehicles.filter((v) => v[2] === 'ambulance')
  return (
    <svg viewBox={`${b.x0} ${-b.y1} ${w} ${h}`} role="img" aria-label={label} className="block w-full select-none" style={{ height, maxHeight: compact ? 360 : 640 }}
      preserveAspectRatio="xMidYMid meet">
      <g>
        {map.roads.map((r, i) => (
          <line key={`rb${i}`} x1={r.x0} x2={r.x1} y1={-r.y0} y2={-r.y1} stroke="var(--panel-2)" strokeWidth="3.6" strokeLinecap="butt" />
        ))}
        {map.roads.map((r, i) => (
          <line key={`rc${i}`} x1={r.x0} x2={r.x1} y1={-r.y0} y2={-r.y1} stroke="var(--line-strong)" strokeWidth="0.1" strokeDasharray="0.5 0.7" />
        ))}
      </g>
      <g>
        {map.vehicles.map((v, i) => {
          const s = VEHICLE[v[2]] || VEHICLE.car
          if (v[2] === 'ambulance') return null
          return <rect key={i} x={v[0] - s.size / 2} y={-v[1] - s.size / 2} width={s.size} height={s.size} rx="0.06" fill={s.color} stroke="var(--bg)" strokeWidth="0.05" />
        })}
        {amb.map((v, i) => (
          <g key={`a${i}`}>
            <circle cx={v[0]} cy={-v[1]} r="1.3" fill="var(--alert)" opacity="0.22" className="dot-live" />
            <polygon points={star(v[0], -v[1], 0.85)} fill="var(--alert)" stroke="var(--bg)" strokeWidth="0.06" />
          </g>
        ))}
      </g>
      <g>
        {map.signals.map((s, i) => (
          <circle key={i} cx={s.x} cy={-s.y} r="0.34" fill={SIGNAL_VAR[s.s]} stroke="var(--fg)" strokeWidth="0.07">
            <title>{`J${s.j + 1} ${s.a}: ${s.s}`}</title>
          </circle>
        ))}
      </g>
      <g fontFamily="JetBrains Mono Variable, JetBrains Mono, monospace" textAnchor="middle" fill="var(--fg)">
        {map.labels.map((l) => (
          <g key={l.j}>
            <rect x={l.x - 1.55} y={-l.y - 1.05} width="3.1" height="2.1" rx="0.3" fill="var(--bg)" fillOpacity="0.82" stroke={l.preempt ? 'var(--warn)' : 'var(--line-strong)'} strokeWidth="0.08" />
            <text x={l.x} y={-l.y - 0.18} fontSize="0.78" fontWeight="700">{`J${l.j}${l.preempt ? ' ⚡' : ''}`}</text>
            <text x={l.x} y={-l.y + 0.72} fontSize="0.62" fill="var(--muted)">{`${l.phase} ${l.timer}s`}</text>
          </g>
        ))}
      </g>
    </svg>
  )
}

export default memo(TrafficMap)

export function MapLegend() {
  const items = [
    ['Car', VEHICLE.car.color], ['Bike', VEHICLE.bike.color], ['Bus', VEHICLE.bus.color], ['Truck', VEHICLE.truck.color],
  ]
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 font-mono text-[10px] uppercase tracking-wider text-muted" aria-label="Map legend">
      <li className="flex items-center gap-1.5"><i className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: SIGNAL_VAR.green }} />green</li>
      <li className="flex items-center gap-1.5"><i className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: SIGNAL_VAR.clearing }} />clearing</li>
      <li className="flex items-center gap-1.5"><i className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: SIGNAL_VAR.red }} />red</li>
      {items.map(([l, c]) => <li key={l} className="flex items-center gap-1.5"><i className="inline-block h-2.5 w-2.5 rounded-[2px]" style={{ background: c }} />{l}</li>)}
      <li className="flex items-center gap-1.5 text-alert">★ ambulance</li>
      <li className="flex items-center gap-1.5 text-warn">⚡ pre-empted</li>
    </ul>
  )
}

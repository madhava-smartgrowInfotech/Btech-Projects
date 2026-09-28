// Small dependency-free SVG charts.

const fmtDate = (s) => {
  const d = new Date(s + 'T00:00:00')
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

export function LineChart({ points, height = 220, unit = 'kg', color = '#059669' }) {
  if (!points.length) return <p className="text-sm text-slate-500 py-8 text-center">No entries yet.</p>
  const W = 640, H = height, pad = { l: 44, r: 16, t: 16, b: 28 }
  const ys = points.map((p) => p.y)
  let min = Math.min(...ys), max = Math.max(...ys)
  if (max - min < 1) { min -= 0.5; max += 0.5 }
  const x = (i) => pad.l + (points.length === 1 ? (W - pad.l - pad.r) / 2 : (i / (points.length - 1)) * (W - pad.l - pad.r))
  const y = (v) => pad.t + (1 - (v - min) / (max - min)) * (H - pad.t - pad.b)
  const ticks = [min, (min + max) / 2, max]
  const step = Math.max(1, Math.ceil(points.length / 7))
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Line chart">
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" />
          <text x={pad.l - 6} y={y(t) + 4} textAnchor="end" fontSize="11" fill="#64748b">{t.toFixed(1)}</text>
        </g>
      ))}
      <polyline fill="none" stroke={color} strokeWidth="2.5" points={points.map((p, i) => `${x(i)},${y(p.y)}`).join(' ')} />
      {points.map((p, i) => (
        <g key={i}>
          <circle cx={x(i)} cy={y(p.y)} r="3.5" fill={color}><title>{`${fmtDate(p.x)}: ${p.y} ${unit}`}</title></circle>
          {i % step === 0 && <text x={x(i)} y={H - 8} textAnchor="middle" fontSize="11" fill="#64748b">{fmtDate(p.x)}</text>}
        </g>
      ))}
    </svg>
  )
}

export function BarChart({ data, height = 240 }) {
  // data: [{x: date, value, target}]
  if (!data.length) return null
  const W = 640, H = height, pad = { l: 44, r: 16, t: 16, b: 28 }
  const max = Math.max(...data.map((d) => Math.max(d.value, d.target))) * 1.1 || 1
  const bw = (W - pad.l - pad.r) / data.length
  const y = (v) => pad.t + (1 - v / max) * (H - pad.t - pad.b)
  const step = Math.max(1, Math.ceil(data.length / 7))
  const ticks = [0, max / 2, max]
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Intake versus target chart">
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" />
          <text x={pad.l - 6} y={y(t) + 4} textAnchor="end" fontSize="11" fill="#64748b">{Math.round(t)}</text>
        </g>
      ))}
      {data.map((d, i) => {
        const within = d.value > 0 && Math.abs(d.value - d.target) / d.target <= 0.1
        const x0 = pad.l + i * bw
        return (
          <g key={i}>
            <rect x={x0 + bw * 0.15} width={bw * 0.7} y={y(d.value)} height={Math.max(0, y(0) - y(d.value))} rx="3"
              fill={d.value === 0 ? '#e2e8f0' : within ? '#10b981' : '#f59e0b'}>
              <title>{`${fmtDate(d.x)}: ${Math.round(d.value)} / ${Math.round(d.target)} kcal`}</title>
            </rect>
            <line x1={x0} x2={x0 + bw} y1={y(d.target)} y2={y(d.target)} stroke="#0f172a" strokeDasharray="4 3" strokeWidth="1.5" />
            {i % step === 0 && <text x={x0 + bw / 2} y={H - 8} textAnchor="middle" fontSize="11" fill="#64748b">{fmtDate(d.x)}</text>}
          </g>
        )
      })}
    </svg>
  )
}

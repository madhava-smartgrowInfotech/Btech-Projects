// Lightweight SVG charts (no chart library needed).
const W = 640
const PAD = { l: 48, r: 44, t: 12, b: 28 }

function ticks(min, max, n = 4) {
  if (min === max) return [min]
  const step = (max - min) / n
  return Array.from({ length: n + 1 }, (_, i) => min + i * step)
}

function extent(values, padFrac = 0.08) {
  const v = values.filter((x) => x != null && !Number.isNaN(x))
  if (!v.length) return [0, 1]
  const lo = Math.min(...v)
  const hi = Math.max(...v)
  const pad = (hi - lo || Math.abs(hi) || 1) * padFrac
  return [lo - pad, hi + pad]
}

const short = (n) => (Math.abs(n) >= 1000 ? `${(n / 1000).toFixed(1)}k` : Math.abs(n) >= 10 ? n.toFixed(0) : n.toFixed(1))

export function LineChart({ labels, series, right, height = 240, yUnit = '', rightUnit = '', highlight, bands, zeroBased = false }) {
  const H = height
  const iw = W - PAD.l - PAD.r
  const ih = H - PAD.t - PAD.b
  const all = series.flatMap((s) => s.values)
  let [lo, hi] = extent(all)
  if (zeroBased) lo = Math.min(0, lo)
  const x = (i) => PAD.l + (labels.length <= 1 ? iw / 2 : (i * iw) / (labels.length - 1))
  const y = (v) => PAD.t + ih - ((v - lo) / (hi - lo || 1)) * ih
  let ry = null
  let rext = [0, 1]
  if (right) {
    rext = extent(right.flatMap((s) => s.values), 0.15)
    ry = (v) => PAD.t + ih - ((v - rext[0]) / (rext[1] - rext[0] || 1)) * ih
  }
  const path = (vals, fy) =>
    vals
      .map((v, i) => (v == null ? null : `${x(i)},${fy(v)}`))
      .filter(Boolean)
      .map((p, i) => (i ? 'L' : 'M') + p)
      .join(' ')
  const every = Math.max(1, Math.ceil(labels.length / 8))
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img">
        {bands?.map((b, i) => (
          <rect key={i} x={x(b.from) - 4} y={PAD.t} width={Math.max(8, x(b.to) - x(b.from) + 8)} height={ih} fill={b.color || '#f1f5f9'} />
        ))}
        {ticks(lo, hi).map((t, i) => (
          <g key={i}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" />
            <text x={PAD.l - 6} y={y(t) + 4} textAnchor="end" fontSize="10" fill="#64748b">
              {short(t)}
            </text>
          </g>
        ))}
        {right &&
          ticks(rext[0], rext[1]).map((t, i) => (
            <text key={i} x={W - PAD.r + 6} y={ry(t) + 4} fontSize="10" fill="#94a3b8">
              {short(t)}
            </text>
          ))}
        {labels.map((l, i) =>
          i % every === 0 || i === labels.length - 1 ? (
            <text key={i} x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill="#64748b">
              {l}
            </text>
          ) : null
        )}
        {highlight != null && <line x1={x(highlight)} x2={x(highlight)} y1={PAD.t} y2={PAD.t + ih} stroke="#f43f5e" strokeDasharray="4 3" />}
        {right?.map((s) => (
          <path key={s.name} d={path(s.values, ry)} fill="none" stroke={s.color} strokeWidth="1.5" strokeDasharray="3 3" />
        ))}
        {series.map((s) => (
          <g key={s.name}>
            <path d={path(s.values, y)} fill="none" stroke={s.color} strokeWidth="2.2" strokeDasharray={s.dashed ? '6 4' : undefined} />
            {s.dots &&
              s.values.map((v, i) =>
                v == null ? null : (
                  <circle key={i} cx={x(i)} cy={y(v)} r={i === highlight ? 5 : 3} fill={i === highlight ? '#f43f5e' : s.color}>
                    <title>{`${labels[i]}: ${v.toFixed(1)} ${yUnit}`}</title>
                  </circle>
                )
              )}
          </g>
        ))}
        <text x={4} y={PAD.t + 2} fontSize="10" fill="#94a3b8">
          {yUnit}
        </text>
        {right && (
          <text x={W - 4} y={PAD.t + 2} fontSize="10" fill="#94a3b8" textAnchor="end">
            {rightUnit}
          </text>
        )}
      </svg>
      <Legend items={[...series, ...(right || [])]} />
    </div>
  )
}

export function BarChart({ categories, series, height = 240, yUnit = '' }) {
  const H = height
  const iw = W - PAD.l - 12
  const ih = H - PAD.t - PAD.b
  const hi = Math.max(...series.flatMap((s) => s.values), 0) * 1.1 || 1
  const y = (v) => PAD.t + ih - (v / hi) * ih
  const gw = iw / categories.length
  const bw = Math.min(28, (gw * 0.75) / series.length)
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img">
        {ticks(0, hi).map((t, i) => (
          <g key={i}>
            <line x1={PAD.l} x2={W - 12} y1={y(t)} y2={y(t)} stroke="#e2e8f0" />
            <text x={PAD.l - 6} y={y(t) + 4} textAnchor="end" fontSize="10" fill="#64748b">
              {short(t)}
            </text>
          </g>
        ))}
        {categories.map((c, ci) => {
          const x0 = PAD.l + ci * gw + (gw - bw * series.length) / 2
          return (
            <g key={c}>
              {series.map((s, si) => (
                <rect
                  key={s.name}
                  x={x0 + si * bw}
                  y={y(s.values[ci])}
                  width={bw - 2}
                  height={Math.max(0, PAD.t + ih - y(s.values[ci]))}
                  rx="2"
                  fill={s.colors?.[ci] || s.color}
                >
                  <title>{`${c} - ${s.name}: ${s.values[ci].toFixed(1)} ${yUnit}`}</title>
                </rect>
              ))}
              <text x={PAD.l + ci * gw + gw / 2} y={H - 8} textAnchor="middle" fontSize="10" fill="#64748b">
                {c}
              </text>
            </g>
          )
        })}
        <text x={4} y={PAD.t + 2} fontSize="10" fill="#94a3b8">
          {yUnit}
        </text>
      </svg>
      <Legend items={series} />
    </div>
  )
}

function Legend({ items }) {
  return (
    <div className="flex flex-wrap gap-4 mt-1 text-xs text-slate-600">
      {items.map((s) => (
        <span key={s.name} className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-1.5 rounded" style={{ background: s.color }} /> {s.name}
        </span>
      ))}
    </div>
  )
}

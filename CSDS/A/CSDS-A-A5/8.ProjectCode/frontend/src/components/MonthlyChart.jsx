import { inr, monthLabel } from '../format'

// Grouped bars per month: ITC available in GSTR-2B vs ITC claimed in GSTR-3B, plus the JEPA deviation line.
export default function MonthlyChart({ monthly }) {
  const W = 720, H = 220, P = { l: 56, r: 40, t: 12, b: 28 }
  const rows = monthly
  const maxV = Math.max(1, ...rows.flatMap((r) => [r.avail || 0, r.claimed || 0]))
  const maxD = Math.max(2, ...rows.map((r) => r.deviation || 0))
  const bw = (W - P.l - P.r) / rows.length
  const y = (v) => P.t + (H - P.t - P.b) * (1 - v / maxV)
  const yd = (v) => P.t + (H - P.t - P.b) * (1 - v / maxD)
  const pts = rows.map((r, i) => (r.deviation ? `${P.l + bw * i + bw / 2},${yd(r.deviation)}` : null)).filter(Boolean)
  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full min-w-[560px]" role="img" aria-label="Monthly ITC and deviation">
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={P.l} x2={W - P.r} y1={y(maxV * f)} y2={y(maxV * f)} stroke="#e2e8f0" />
            <text x={P.l - 6} y={y(maxV * f) + 4} fontSize="10" textAnchor="end" fill="#64748b">{inr(maxV * f)}</text>
          </g>
        ))}
        <text x={W - P.r + 6} y={yd(maxD) + 4} fontSize="10" fill="#7c3aed">{maxD.toFixed(0)}x</text>
        {rows.map((r, i) => {
          const x = P.l + bw * i
          return (
            <g key={r.month}>
              {r.present ? (
                <>
                  <rect x={x + bw * 0.14} width={bw * 0.34} y={y(r.avail || 0)} height={H - P.b - y(r.avail || 0)} fill="#94a3b8" rx="2">
                    <title>{`GSTR-2B available ${inr(r.avail)}`}</title>
                  </rect>
                  <rect x={x + bw * 0.52} width={bw * 0.34} y={y(r.claimed || 0)} height={H - P.b - y(r.claimed || 0)}
                    fill={(r.claimed || 0) > 1.2 * (r.avail || 0) + 50000 ? '#dc2626' : '#4f46e5'} rx="2">
                    <title>{`GSTR-3B claimed ${inr(r.claimed)} · deviation ${r.deviation?.toFixed(1)}x`}</title>
                  </rect>
                </>
              ) : (
                <text x={x + bw / 2} y={H - P.b - 6} fontSize="9" textAnchor="middle" fill="#94a3b8">no return</text>
              )}
              <text x={x + bw / 2} y={H - 10} fontSize="10" textAnchor="middle" fill="#475569">{monthLabel(r.month)}</text>
            </g>
          )
        })}
        {pts.length > 1 && <polyline points={pts.join(' ')} fill="none" stroke="#7c3aed" strokeWidth="1.8" strokeDasharray="4 3" />}
      </svg>
      <div className="flex flex-wrap gap-4 text-[11px] text-slate-600 mt-1 px-1">
        <span className="flex items-center gap-1"><i className="w-3 h-3 bg-slate-400 inline-block rounded-sm" />ITC available (GSTR-2B)</span>
        <span className="flex items-center gap-1"><i className="w-3 h-3 bg-indigo-600 inline-block rounded-sm" />ITC claimed (GSTR-3B)</span>
        <span className="flex items-center gap-1"><i className="w-3 h-3 bg-red-600 inline-block rounded-sm" />claimed well above 2B</span>
        <span className="flex items-center gap-1"><i className="w-4 border-t-2 border-dashed border-violet-600 inline-block" />JEPA deviation (x typical)</span>
      </div>
    </div>
  )
}

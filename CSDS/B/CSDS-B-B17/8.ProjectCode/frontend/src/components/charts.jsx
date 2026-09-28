import { EMOTION_COLOR } from './ui.jsx'
import { fmtTime } from '../api.js'

export function HBars({ rows, valueKey = 'count', labelKey = 'label', color = '#4f46e5', format = (v) => v }) {
  const max = Math.max(1, ...rows.map((r) => r[valueKey] || 0))
  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <div key={r[labelKey]} className="text-sm">
          <div className="mb-0.5 flex justify-between gap-2">
            <span className="truncate">{String(r[labelKey]).replaceAll('_', ' ')}</span>
            <span className="font-medium text-slate-600">{format(r[valueKey])}</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100">
            <div className="h-2 rounded-full" style={{ width: `${(100 * (r[valueKey] || 0)) / max}%`, background: color }} />
          </div>
        </div>
      ))}
    </div>
  )
}

/** Daily calls (bars) with average customer sentiment (line, -1..1). */
export function TrendChart({ data }) {
  const W = 640, H = 220, P = { l: 36, r: 36, t: 14, b: 28 }
  const iw = W - P.l - P.r, ih = H - P.t - P.b
  const maxCalls = Math.max(1, ...data.map((d) => d.calls))
  const bw = Math.min(28, (iw / Math.max(1, data.length)) * 0.6)
  const x = (i) => P.l + (iw * (i + 0.5)) / Math.max(1, data.length)
  const ys = (v) => P.t + ih * (1 - (v + 1) / 2)
  const pts = data.map((d, i) => (d.sentiment == null ? null : [x(i), ys(d.sentiment)])).filter(Boolean)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Call volume and sentiment trend">
      <line x1={P.l} x2={W - P.r} y1={ys(0)} y2={ys(0)} stroke="#e2e8f0" strokeDasharray="4 4" />
      {[-1, 0, 1].map((v) => (
        <text key={v} x={W - P.r + 6} y={ys(v) + 4} fontSize="10" fill="#0d9488">{v > 0 ? '+1' : v}</text>
      ))}
      <text x={4} y={P.t + 8} fontSize="10" fill="#6366f1">{maxCalls}</text>
      <text x={4} y={P.t + ih} fontSize="10" fill="#6366f1">0</text>
      {data.map((d, i) => {
        const h = (ih * d.calls) / maxCalls
        return (
          <g key={d.date}>
            <rect x={x(i) - bw / 2} y={P.t + ih - h} width={bw} height={h} rx="3" fill="#c7d2fe">
              <title>{`${d.date}: ${d.calls} call(s)`}</title>
            </rect>
            {(data.length <= 16 || i % Math.ceil(data.length / 12) === 0) && (
              <text x={x(i)} y={H - 8} fontSize="10" textAnchor="middle" fill="#64748b">{d.date.slice(5)}</text>
            )}
          </g>
        )
      })}
      {pts.length > 1 && <polyline points={pts.map((p) => p.join(',')).join(' ')} fill="none" stroke="#0d9488" strokeWidth="2" />}
      {data.map((d, i) =>
        d.sentiment == null ? null : (
          <circle key={d.date} cx={x(i)} cy={ys(d.sentiment)} r="3.5" fill="#0d9488">
            <title>{`${d.date}: sentiment ${d.sentiment.toFixed(2)}`}</title>
          </circle>
        ),
      )}
    </svg>
  )
}

/** Emotion timeline: customer valence over the call, dots coloured by emotion, flags as markers. */
export function EmotionTimeline({ segments, flags = [], duration, showAgent, onSeek, current }) {
  const W = 760, H = 200, P = { l: 34, r: 12, t: 16, b: 26 }
  const iw = W - P.l - P.r, ih = H - P.t - P.b
  const T = Math.max(duration || 0, ...segments.map((s) => s.end), 1)
  const x = (t) => P.l + (iw * t) / T
  const y = (v) => P.t + ih * (1 - (v + 1) / 2)
  const line = (spk) =>
    segments
      .filter((s) => s.speaker === spk)
      .map((s) => [x((s.start + s.end) / 2), y(s.valence ?? 0)])
  const cust = line('customer')
  const agent = line('agent')
  const ticks = Array.from({ length: 6 }, (_, i) => (T * i) / 5)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Emotion timeline">
      <rect x={P.l} y={y(1)} width={iw} height={y(0.2) - y(1)} fill="#f0fdf4" />
      <rect x={P.l} y={y(-0.3)} width={iw} height={y(-1) - y(-0.3)} fill="#fef2f2" />
      <line x1={P.l} x2={W - P.r} y1={y(0)} y2={y(0)} stroke="#cbd5e1" strokeDasharray="4 4" />
      <text x={4} y={y(1) + 10} fontSize="10" fill="#16a34a">+1</text>
      <text x={8} y={y(0) + 4} fontSize="10" fill="#64748b">0</text>
      <text x={6} y={y(-1)} fontSize="10" fill="#dc2626">-1</text>
      {ticks.map((t) => (
        <text key={t} x={x(t)} y={H - 6} fontSize="10" textAnchor="middle" fill="#64748b">{fmtTime(t)}</text>
      ))}
      {segments.map((s, i) => (
        <rect
          key={`b${i}`}
          x={x(s.start)}
          y={s.speaker === 'agent' ? H - P.b - 6 : H - P.b - 3}
          width={Math.max(1, x(s.end) - x(s.start))}
          height="3"
          fill={s.speaker === 'agent' ? '#a5b4fc' : '#fdba74'}
        />
      ))}
      {showAgent && agent.length > 1 && (
        <polyline points={agent.map((p) => p.join(',')).join(' ')} fill="none" stroke="#818cf8" strokeWidth="1.5" strokeDasharray="5 4" />
      )}
      {cust.length > 1 && <polyline points={cust.map((p) => p.join(',')).join(' ')} fill="none" stroke="#334155" strokeWidth="2" />}
      {flags.map((f, i) => (
        <g key={`f${i}`}>
          <line x1={x(f.t)} x2={x(f.t)} y1={P.t} y2={H - P.b} stroke={f.severity === 'high' ? '#dc2626' : '#f59e0b'} strokeDasharray="2 3" />
          <text x={x(f.t) + 3} y={P.t + 8} fontSize="11" fill={f.severity === 'high' ? '#dc2626' : '#d97706'}>⚑</text>
        </g>
      ))}
      {segments
        .filter((s) => s.speaker === 'customer' || showAgent)
        .map((s, i) => (
          <circle
            key={`c${i}`}
            cx={x((s.start + s.end) / 2)}
            cy={y(s.valence ?? 0)}
            r={s.speaker === 'customer' ? 6 : 4}
            fill={EMOTION_COLOR[s.emotion] || '#64748b'}
            stroke="white"
            strokeWidth="1.5"
            className="cursor-pointer"
            onClick={() => onSeek?.(s.start)}
          >
            <title>{`${fmtTime(s.start)} ${s.speaker}: ${s.emotion} (${(s.valence ?? 0).toFixed(2)}) - ${s.text}`}</title>
          </circle>
        ))}
      {current != null && <line x1={x(current)} x2={x(current)} y1={P.t} y2={H - P.b} stroke="#4f46e5" strokeWidth="1.5" />}
    </svg>
  )
}

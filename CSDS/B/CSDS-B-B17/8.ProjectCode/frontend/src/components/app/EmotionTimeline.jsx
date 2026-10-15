import { EMOTION_COLOR, fmtTime } from '../../lib/format'

/** Customer valence over the call: dots coloured by emotion, flag markers, playhead. Click or press Enter on a dot to seek. */
export default function EmotionTimeline({ segments, flags = [], duration, showAgent, onSeek, current }) {
  const W = 760
  const H = 220
  const P = { l: 34, r: 12, t: 16, b: 30 }
  const iw = W - P.l - P.r
  const ih = H - P.t - P.b
  const T = Math.max(duration || 0, ...segments.map((s) => s.end), 1)
  const x = (t) => P.l + (iw * t) / T
  const y = (v) => P.t + ih * (1 - (v + 1) / 2)
  const line = (spk) => segments.filter((s) => s.speaker === spk).map((s) => [x((s.start + s.end) / 2), y(s.valence ?? 0)])
  const cust = line('customer')
  const agent = line('agent')
  const ticks = Array.from({ length: 6 }, (_, i) => (T * i) / 5)
  return (
    <div className="tl-wrap" data-lenis-prevent>
      <svg viewBox={`0 0 ${W} ${H}`} className="tl-svg" role="group" aria-label="Emotion timeline of the call">
        <rect x={P.l} y={y(1)} width={iw} height={y(0.2) - y(1)} fill="var(--lime)" fillOpacity="0.28" />
        <rect x={P.l} y={y(-0.3)} width={iw} height={y(-1) - y(-0.3)} fill="var(--coral)" fillOpacity="0.28" />
        <rect x={P.l} y={P.t} width={iw} height={ih} fill="none" stroke="var(--line)" strokeWidth="3" />
        <line x1={P.l} x2={W - P.r} y1={y(0)} y2={y(0)} stroke="var(--line)" strokeDasharray="5 4" strokeWidth="2" />
        <text x={4} y={y(1) + 10}>+1</text>
        <text x={12} y={y(0) + 4}>0</text>
        <text x={6} y={y(-1)}>-1</text>
        {ticks.map((t) => (
          <text key={t} x={x(t)} y={H - 8} textAnchor="middle">
            {fmtTime(t)}
          </text>
        ))}
        {segments.map((s, i) => (
          <rect
            key={`b${i}`}
            x={x(s.start)}
            y={s.speaker === 'agent' ? H - P.b - 8 : H - P.b - 4}
            width={Math.max(1, x(s.end) - x(s.start))}
            height="4"
            fill={s.speaker === 'agent' ? 'var(--sky)' : 'var(--amber)'}
          />
        ))}
        {showAgent && agent.length > 1 && (
          <polyline points={agent.map((p) => p.join(',')).join(' ')} fill="none" stroke="var(--fg)" strokeWidth="2" strokeDasharray="6 5" strokeOpacity="0.6" />
        )}
        {cust.length > 1 && <polyline points={cust.map((p) => p.join(',')).join(' ')} fill="none" stroke="var(--fg)" strokeWidth="3.5" strokeLinejoin="miter" />}
        {flags.map((f, i) => (
          <g key={`f${i}`}>
            <line x1={x(f.t)} x2={x(f.t)} y1={P.t} y2={H - P.b} stroke={f.severity === 'high' ? 'var(--coral)' : 'var(--amber)'} strokeDasharray="3 3" strokeWidth="3" />
            <text x={x(f.t) + 4} y={P.t + 10} style={{ fill: 'var(--fg)' }}>
              ⚑
            </text>
          </g>
        ))}
        {segments
          .filter((s) => s.speaker === 'customer' || showAgent)
          .map((s, i) => {
            const r = s.speaker === 'customer' ? 7 : 5
            const cx = x((s.start + s.end) / 2)
            const cy = y(s.valence ?? 0)
            return (
              <rect
                key={`c${i}`}
                className="tl-dot"
                x={cx - r}
                y={cy - r}
                width={r * 2}
                height={r * 2}
                fill={EMOTION_COLOR[s.emotion] || '#888'}
                tabIndex={0}
                role="button"
                aria-label={`${fmtTime(s.start)} ${s.speaker}, ${s.emotion}. Jump to this moment.`}
                onClick={() => onSeek?.(s.start)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onSeek?.(s.start)
                  }
                }}
              >
                <title>{`${fmtTime(s.start)} ${s.speaker}: ${s.emotion} (${(s.valence ?? 0).toFixed(2)}) - ${s.text}`}</title>
              </rect>
            )
          })}
        {current != null && current > 0 && <line x1={x(current)} x2={x(current)} y1={P.t} y2={H - P.b} stroke="var(--fg)" strokeWidth="3" />}
      </svg>
    </div>
  )
}

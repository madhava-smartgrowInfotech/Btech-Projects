/* TrendCast chart additions in the same Neo Brutal style as Charts.jsx: flat colour, thick axes, no gradients.
   Lazy-loaded with the pages that use them (Recharts stays in the 'charts' chunk). */
import { Bar, BarChart, CartesianGrid, ComposedChart, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BrutalTip, PALETTE, useChartTheme } from './Charts'

const NUM = (v) => (typeof v === 'number' ? (Math.abs(v) >= 100 ? Math.round(v).toLocaleString() : Number(v.toFixed(3)).toString()) : v)

function tickProps(fg) {
  return { fill: fg, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fontWeight: 600 }
}

function sparseInterval(n, narrow) {
  const target = narrow ? 4 : 8
  return Math.max(0, Math.ceil(n / target) - 1)
}

function Legend({ items }) {
  return (
    <div className="legend" aria-hidden="true">
      {items.map((s) => (
        <span key={s.key || s.name}>
          <i style={{ background: s.color }} />
          {s.name}
        </span>
      ))}
    </div>
  )
}

/** Thick flat time-series line(s). series: [{key, name, color, dashed}] */
export function LineBlocks({ data, xKey, series, height = 300, dots = false }) {
  const { fg, grid, animate, narrow } = useChartTheme()
  const tick = tickProps(fg)
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="chart-box" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 12, right: 12, left: -4, bottom: 4 }}>
            <CartesianGrid stroke={grid} vertical={false} />
            <XAxis dataKey={xKey} stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} interval={sparseInterval(data.length, narrow)} height={30} />
            <YAxis stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} width={46} tickFormatter={NUM} />
            <Tooltip content={<BrutalTip />} cursor={{ stroke: fg, strokeWidth: 2 }} />
            {series.map((s) => (
              <Line
                key={s.key}
                type="linear"
                dataKey={s.key}
                name={s.name}
                stroke={s.color || fg}
                strokeWidth={s.dashed ? 3 : 4}
                strokeDasharray={s.dashed ? '8 6' : undefined}
                dot={dots ? { r: 4, fill: s.color || fg, stroke: PALETTE.ink, strokeWidth: 2 } : false}
                activeDot={{ r: 6, fill: PALETTE.lime, stroke: PALETTE.ink, strokeWidth: 3 }}
                isAnimationActive={animate}
                animationDuration={700}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {series.length > 1 && <Legend items={series.map((s) => ({ ...s, color: s.color || fg }))} />}
    </div>
  )
}

/** Horizontal ranked bars (top products, feature importance). */
export function HBarBlocks({ data, labelKey, valueKey, name = 'Value', color = PALETTE.lime, height, labelWidth = 150 }) {
  const { fg, animate } = useChartTheme()
  const tick = tickProps(fg)
  const h = height || Math.max(200, data.length * 32 + 40)
  return (
    <div className="chart-box" style={{ height: h }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 0, bottom: 4 }} barCategoryGap="18%">
          <CartesianGrid stroke="transparent" horizontal={false} />
          <XAxis type="number" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} tickFormatter={NUM} />
          <YAxis type="category" dataKey={labelKey} stroke={fg} strokeWidth={3} tick={tick} tickLine={false} width={labelWidth} interval={0} />
          <Tooltip content={<BrutalTip labelKey={labelKey} />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
          <Bar dataKey={valueKey} name={name} fill={color} stroke={PALETTE.ink} strokeWidth={3} isAnimationActive={animate} animationDuration={700} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Two distributions as side-by-side blocks (source vs target). series: [{key, name, color}] */
export function GroupedBlocks({ data, xKey, series, height = 280 }) {
  const { fg, animate, narrow } = useChartTheme()
  const tick = tickProps(fg)
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="chart-box" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 12, right: 8, left: -4, bottom: 4 }} barCategoryGap="6%" barGap={0}>
            <CartesianGrid stroke="transparent" vertical={false} />
            <XAxis dataKey={xKey} stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} interval={sparseInterval(data.length, narrow)} height={30} />
            <YAxis stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} width={46} tickFormatter={NUM} />
            <Tooltip content={<BrutalTip />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
            {series.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color} stroke={PALETTE.ink} strokeWidth={2} isAnimationActive={animate} animationDuration={700} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <Legend items={series} />
    </div>
  )
}

/**
 * Horizontal box plot drawn in SVG from precomputed stats.
 * boxes: [{label, color, min, q1, median, q3, max, mean}]
 */
export function BoxBlocks({ boxes, height = 190, valueLabel }) {
  const { fg } = useChartTheme()
  const lo = Math.min(...boxes.map((b) => b.min))
  const hi = Math.max(...boxes.map((b) => b.max))
  const span = hi - lo || 1
  const W = 600
  const padL = 70
  const padR = 20
  const x = (v) => padL + ((v - lo) / span) * (W - padL - padR)
  const rowH = (height - 40) / boxes.length
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => lo + t * span)
  return (
    <div className="chart-box" style={{ height }}>
      <svg
        viewBox={`0 0 ${W} ${height}`}
        width="100%"
        height="100%"
        role="img"
        aria-label={`Box plot comparing ${boxes.map((b) => b.label).join(' and ')}${valueLabel ? ` for ${valueLabel}` : ''}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {boxes.map((b, i) => {
          const cy = 18 + rowH * i + rowH / 2
          const bh = Math.min(44, rowH * 0.6)
          return (
            <g key={b.label}>
              <text x={padL - 10} y={cy + 4} textAnchor="end" fill={fg} fontFamily="IBM Plex Mono, monospace" fontSize="12" fontWeight="700">
                {b.label}
              </text>
              <line x1={x(b.min)} x2={x(b.q1)} y1={cy} y2={cy} stroke={fg} strokeWidth="3" />
              <line x1={x(b.q3)} x2={x(b.max)} y1={cy} y2={cy} stroke={fg} strokeWidth="3" />
              <line x1={x(b.min)} x2={x(b.min)} y1={cy - 9} y2={cy + 9} stroke={fg} strokeWidth="3" />
              <line x1={x(b.max)} x2={x(b.max)} y1={cy - 9} y2={cy + 9} stroke={fg} strokeWidth="3" />
              <rect x={x(b.q1)} y={cy - bh / 2} width={Math.max(3, x(b.q3) - x(b.q1))} height={bh} fill={b.color} stroke={PALETTE.ink} strokeWidth="3" />
              <line x1={x(b.median)} x2={x(b.median)} y1={cy - bh / 2} y2={cy + bh / 2} stroke={PALETTE.ink} strokeWidth="4" />
              <rect x={x(b.mean) - 5} y={cy - 5} width="10" height="10" fill={PALETTE.coral} stroke={PALETTE.ink} strokeWidth="2" />
            </g>
          )
        })}
        <line x1={padL} x2={W - padR} y1={height - 24} y2={height - 24} stroke={fg} strokeWidth="3" />
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={x(t)} x2={x(t)} y1={height - 24} y2={height - 18} stroke={fg} strokeWidth="2" />
            <text x={x(t)} y={height - 5} textAnchor={i === 0 ? 'start' : i === ticks.length - 1 ? 'end' : 'middle'} fill={fg} fontFamily="IBM Plex Mono, monospace" fontSize="11" fontWeight="600">
              {NUM(t)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}

/** History (solid) then forecast (dashed) split at the transition date. rows: [{date, history, forecast}] */
export function ForecastBlocks({ rows, height = 320 }) {
  const { fg, grid, animate, narrow } = useChartTheme()
  const tick = tickProps(fg)
  const firstForecast = rows.find((r) => r.forecast !== null && r.forecast !== undefined)
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="chart-box" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 12, right: 12, left: -4, bottom: 4 }}>
            <CartesianGrid stroke={grid} vertical={false} />
            <XAxis dataKey="date" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} interval={sparseInterval(rows.length, narrow)} height={30} />
            <YAxis stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} width={40} />
            <Tooltip content={<BrutalTip />} cursor={{ stroke: fg, strokeWidth: 2 }} />
            {firstForecast && <ReferenceLine x={firstForecast.date} stroke={PALETTE.coral} strokeWidth={3} strokeDasharray="4 4" />}
            <Line type="linear" dataKey="history" name="Historical demand" stroke={fg} strokeWidth={3} dot={false} isAnimationActive={animate} connectNulls={false} />
            <Line
              type="linear"
              dataKey="forecast"
              name="Forecast"
              stroke={PALETTE.coral}
              strokeWidth={4}
              strokeDasharray="8 6"
              dot={{ r: 4, fill: PALETTE.lime, stroke: PALETTE.ink, strokeWidth: 2 }}
              isAnimationActive={animate}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <Legend items={[{ name: 'Historical demand', color: fg }, { name: 'Forecast', color: PALETTE.coral }]} />
    </div>
  )
}

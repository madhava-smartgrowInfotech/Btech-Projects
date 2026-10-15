/* Recharts wrappers in the Neo Brutal style: flat colour blocks, thick axes, accent fills,
   no gradients, no soft shadows. Lazy-loaded with the pages that use them. */
import { Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTheme } from '../../lib/theme'
import { useReducedMotion } from '../../lib/motion'

export const PALETTE = { lime: '#C8FF2E', coral: '#FF5C39', sky: '#7CC6FF', amber: '#FFD23F', ink: '#111111', paper: '#FAF7F0' }

function useChartTheme() {
  const { theme } = useTheme()
  const reduced = useReducedMotion()
  const fg = theme === 'dark' ? PALETTE.paper : PALETTE.ink
  const narrow = typeof window !== 'undefined' && window.innerWidth < 640
  return { fg, grid: theme === 'dark' ? '#3a3a3a' : '#d9d3c4', animate: !reduced, narrow }
}

function BrutalTip({ active, payload, label, labelKey, format }) {
  if (!active || !payload?.length) return null
  const title = labelKey ? payload[0]?.payload?.[labelKey] : label
  return (
    <div className="chart-tip">
      <div className="t">{title}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="row" style={{ '--gap': '6px' }}>
          <i style={{ width: 10, height: 10, background: p.color || p.fill, border: '2px solid currentColor', display: 'inline-block' }} />
          {p.name}: <strong>{format ? format(p.value) : p.value}</strong>
        </div>
      ))}
    </div>
  )
}

function axes(fg, xKey, { angle } = {}) {
  const tick = { fill: fg, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fontWeight: 600 }
  return [
    <CartesianGrid key="g" stroke="transparent" vertical={false} />,
    <XAxis
      key="x"
      dataKey={xKey}
      stroke={fg}
      strokeWidth={3}
      tick={tick}
      tickLine={{ stroke: fg, strokeWidth: 2 }}
      interval={0}
      angle={angle}
      textAnchor={angle ? 'end' : 'middle'}
      height={angle ? 60 : 30}
    />,
    <YAxis key="y" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} allowDecimals={false} width={36} />,
  ]
}

/** Single-series bar chart. data: [{[xKey], [yKey]}] */
export function BarBlocks({ data, xKey, yKey, name, color = PALETTE.lime, colorFn, height = 280, labelKey }) {
  const { fg, animate, narrow } = useChartTheme()
  return (
    <div className="chart-box" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 12, right: 8, left: -8, bottom: 4 }} barCategoryGap="22%">
          {axes(fg, xKey, { angle: data.length > 6 || (narrow && data.length > 3) ? -35 : 0 })}
          <Tooltip content={<BrutalTip labelKey={labelKey} />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
          <Bar dataKey={yKey} name={name} fill={color} stroke={PALETTE.ink} strokeWidth={3} isAnimationActive={animate} animationDuration={700}>
            {colorFn && data.map((d, i) => <Cell key={i} fill={colorFn(d)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Stacked bars. series: [{key, name, color}] */
export function StackedBlocks({ data, xKey, series, height = 280 }) {
  const { fg, animate, narrow } = useChartTheme()
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="chart-box" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 12, right: 8, left: -8, bottom: 4 }} barCategoryGap="22%">
            {axes(fg, xKey, { angle: narrow && data.length > 3 ? -35 : 0 })}
            <Tooltip content={<BrutalTip />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
            {series.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.name} stackId="a" fill={s.color} stroke={PALETTE.ink} strokeWidth={3} isAnimationActive={animate} animationDuration={700} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="legend" aria-hidden="true">
        {series.map((s) => (
          <span key={s.key}>
            <i style={{ background: s.color }} />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  )
}

/** Horizontal bars with the category label on the left. rows: [{[labelKey], [valueKey]}] */
export function HBarBlocks({ rows, labelKey = 'label', valueKey = 'count', name = 'Count', color = PALETTE.lime, colorFn, format, domainMax, ariaLabel }) {
  const { fg, animate, narrow } = useChartTheme()
  const data = rows.map((r) => ({ ...r, [labelKey]: String(r[labelKey]).replaceAll('_', ' ') }))
  const height = Math.max(120, data.length * 38 + 40)
  const tick = { fill: fg, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fontWeight: 600 }
  const fmt = format ? (v) => format(v) : undefined
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={ariaLabel || `${name} by ${labelKey}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 0, bottom: 4 }} barCategoryGap="20%">
          <CartesianGrid stroke="transparent" />
          <XAxis type="number" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} tickFormatter={fmt} domain={[0, domainMax || 'auto']} allowDecimals={!!format} />
          <YAxis type="category" dataKey={labelKey} stroke={fg} strokeWidth={3} tick={tick} tickLine={false} width={narrow ? 96 : 160} interval={0} />
          <Tooltip content={<BrutalTip labelKey={labelKey} format={fmt} />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
          <Bar dataKey={valueKey} name={name} maxBarSize={30} fill={color} stroke={PALETTE.ink} strokeWidth={3} isAnimationActive={animate} animationDuration={700}>
            {colorFn && data.map((d, i) => <Cell key={i} fill={colorFn(d)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Daily calls (bars, left axis) with average customer sentiment (line, right axis, -1..1). */
export function TrendBlocks({ data, height = 300 }) {
  const { fg, animate } = useChartTheme()
  const tick = { fill: fg, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fontWeight: 600 }
  const rows = data.map((d) => ({ ...d, day: d.date.slice(5) }))
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="chart-box" style={{ height }} role="img" aria-label="Calls per day and average customer sentiment">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 12, right: 0, left: -8, bottom: 4 }}>
            <CartesianGrid stroke="transparent" />
            <XAxis dataKey="day" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} minTickGap={12} />
            <YAxis yAxisId="calls" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} allowDecimals={false} width={36} />
            <YAxis yAxisId="sent" orientation="right" domain={[-1, 1]} ticks={[-1, 0, 1]} stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} width={36} />
            <ReferenceLine yAxisId="sent" y={0} stroke={fg} strokeDasharray="4 4" />
            <Tooltip content={<BrutalTip labelKey="date" />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
            <Bar yAxisId="calls" dataKey="calls" name="Calls" maxBarSize={64} fill={PALETTE.lime} stroke={PALETTE.ink} strokeWidth={3} isAnimationActive={animate} animationDuration={700} />
            <Line
              yAxisId="sent"
              dataKey="sentiment"
              name="Avg sentiment"
              type="linear"
              stroke={PALETTE.coral}
              strokeWidth={4}
              connectNulls
              dot={{ r: 5, fill: PALETTE.coral, stroke: PALETTE.ink, strokeWidth: 2 }}
              isAnimationActive={animate}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="legend" aria-hidden="true">
        <span>
          <i style={{ background: PALETTE.lime }} />
          Calls per day (left)
        </span>
        <span>
          <i style={{ background: PALETTE.coral }} />
          Avg customer sentiment (right, -1 to +1)
        </span>
      </div>
    </div>
  )
}

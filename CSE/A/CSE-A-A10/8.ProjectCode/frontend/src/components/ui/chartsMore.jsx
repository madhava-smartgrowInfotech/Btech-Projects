import { useId, useRef } from 'react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ErrorBar, Legend, Line, LineChart, ReferenceLine,
  Scatter, ScatterChart, Tooltip as RTooltip, XAxis, YAxis, ZAxis,
} from 'recharts'
import { useSize } from '../../lib/reduced'
import { ChartFrame, MonoTooltip, useChartTheme } from './charts'

// Chart wrappers on top of the kit's ChartFrame / MonoTooltip / theme tokens (thin strokes, monospace labels).
const MARGIN = { top: 8, right: 12, bottom: 4, left: 0 }
const MONO = 'JetBrains Mono, monospace'
const fmtTick = (v) => (typeof v === 'number' && !Number.isInteger(v) ? +v.toFixed(1) : v)
const tip = (valueFormat, labelFormat) => (
  <RTooltip cursor={{ stroke: 'var(--line-strong)' }} content={<MonoTooltip valueFormat={valueFormat} labelFormat={labelFormat} />} />
)
const axisLabel = (value, tokens, extra = {}) => ({ value, fill: tokens.dim, fontSize: 10, fontFamily: MONO, ...extra })

// Filled area over time (queue length etc.).
export function AreaSeries({ data, xKey, yKey, name, tone = 'ok', height = 230, label, xName, valueFormat, labelFormat }) {
  const { tokens, axis, grid } = useChartTheme()
  const gid = `ar${useId().replace(/[^a-zA-Z0-9]/g, '')}`
  const color = tokens[tone] || tokens.ok
  return (
    <ChartFrame height={height} label={label}>
      {({ width, height: h }) => (
        <AreaChart width={width} height={h} data={data} margin={{ ...MARGIN, bottom: xName ? 16 : 4 }}>
          <defs>
            <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid {...grid} vertical={false} />
          <XAxis dataKey={xKey} type="number" domain={['dataMin', 'dataMax']} minTickGap={40} {...axis}
            label={xName ? axisLabel(xName, tokens, { position: 'insideBottom', offset: -8 }) : undefined} />
          <YAxis {...axis} width={34} allowDecimals />
          {tip(valueFormat, labelFormat)}
          <Area type="monotone" dataKey={yKey} name={name} stroke={color} strokeWidth={1.6} fill={`url(#${gid})`} dot={false} isAnimationActive={false} />
        </AreaChart>
      )}
    </ChartFrame>
  )
}

// Grouped / stacked / single-series vertical bars. bars: [{key, label, color}].
// `colorKey` colours each bar from a row field; `errorKey` adds whiskers to the first series.
export function BarsChart({ data, xKey, bars, stacked = false, height = 260, label, valueFormat, labelFormat, colorKey, errorKey, legend = false, yName, xName, topLabels = false }) {
  const { animate, axis, grid, tokens } = useChartTheme()
  return (
    <ChartFrame height={height} label={label} crosshair={false}>
      {({ width, height: h }) => (
        <BarChart width={width} height={h} data={data} margin={{ ...MARGIN, bottom: xName ? 18 : 4 }} barCategoryGap="22%">
          <CartesianGrid {...grid} vertical={false} />
          <XAxis dataKey={xKey} interval={0} tickMargin={6} {...axis}
            label={xName ? axisLabel(xName, tokens, { position: 'insideBottom', offset: -8 }) : undefined} />
          <YAxis {...axis} width={yName ? 46 : 38} allowDecimals
            label={yName ? axisLabel(yName, tokens, { angle: -90, position: 'insideLeft', offset: 8 }) : undefined} />
          {tip(valueFormat, labelFormat)}
          {legend && <Legend verticalAlign="top" height={26} wrapperStyle={{ fontSize: 10, fontFamily: MONO, color: tokens.muted }} iconType="square" iconSize={8} />}
          {bars.map((b, i) => (
            <Bar key={b.key} dataKey={b.key} name={b.label} fill={b.color} stackId={stacked ? 's' : undefined}
              radius={stacked ? 0 : [2, 2, 0, 0]} isAnimationActive={animate} animationDuration={600}
              label={topLabels ? { position: 'insideBottom', offset: 6, fill: 'var(--bg)', fontSize: 11, fontWeight: 700, fontFamily: MONO, formatter: (v) => (valueFormat ? valueFormat(v) : v) } : undefined}>
              {colorKey && data.map((row, k) => <Cell key={k} fill={row[colorKey]} />)}
              {errorKey && i === 0 && <ErrorBar dataKey={errorKey} width={4} stroke={tokens.muted} strokeWidth={1.2} />}
            </Bar>
          ))}
        </BarChart>
      )}
    </ChartFrame>
  )
}

// Horizontal bars (feature importance).
export function HBars({ data, labelKey, valueKey, tone = 'ok', height = 260, label, valueFormat, name = 'Value' }) {
  const { animate, axis, grid, tokens } = useChartTheme()
  return (
    <ChartFrame height={height} label={label} crosshair={false}>
      {({ width, height: h }) => (
        <BarChart width={width} height={h} data={data} layout="vertical" margin={{ top: 4, right: 18, bottom: 4, left: 4 }} barCategoryGap="18%">
          <CartesianGrid {...grid} horizontal={false} />
          <XAxis type="number" tickFormatter={fmtTick} {...axis} />
          <YAxis type="category" dataKey={labelKey} {...axis} width={118} interval={0} />
          {tip(valueFormat)}
          <Bar dataKey={valueKey} name={name} fill={tokens[tone]} radius={[0, 2, 2, 0]} isAnimationActive={animate} animationDuration={600} />
        </BarChart>
      )}
    </ChartFrame>
  )
}

// Multi-series line chart. lines: [{key, label, color, width, dots}]
export function LinesChart({ data, xKey, lines, height = 280, label, xName, yName, valueFormat, labelFormat, legend = true }) {
  const { animate, axis, grid, tokens } = useChartTheme()
  return (
    <ChartFrame height={height} label={label}>
      {({ width, height: h }) => (
        <LineChart width={width} height={h} data={data} margin={{ ...MARGIN, bottom: xName ? 18 : 4 }}>
          <CartesianGrid {...grid} vertical={false} />
          <XAxis dataKey={xKey} type="number" domain={['dataMin', 'dataMax']} minTickGap={30} {...axis}
            label={xName ? axisLabel(xName, tokens, { position: 'insideBottom', offset: -8 }) : undefined} />
          <YAxis {...axis} width={yName ? 46 : 38} allowDecimals
            label={yName ? axisLabel(yName, tokens, { angle: -90, position: 'insideLeft', offset: 8 }) : undefined} />
          {tip(valueFormat, labelFormat)}
          {legend && <Legend verticalAlign="top" height={26} wrapperStyle={{ fontSize: 10, fontFamily: MONO, color: tokens.muted }} iconType="plainline" />}
          {lines.map((l) => (
            <Line key={l.key} type="monotone" dataKey={l.key} name={l.label} stroke={l.color} strokeWidth={l.width || 1.6}
              dot={l.dots ? { r: 3 } : false} isAnimationActive={animate} animationDuration={700} />
          ))}
        </LineChart>
      )}
    </ChartFrame>
  )
}

// Predicted-vs-actual scatter with a dashed ideal line.
export function ScatterPlot({ data, xKey, yKey, xName, yName, ideal, height = 300, label, tone = 'cyan' }) {
  const { axis, grid, tokens } = useChartTheme()
  return (
    <ChartFrame height={height} label={label}>
      {({ width, height: h }) => (
        <ScatterChart width={width} height={h} margin={{ top: 8, right: 14, bottom: 24, left: 4 }}>
          <CartesianGrid {...grid} />
          <XAxis type="number" dataKey={xKey} name={xName} domain={[0, 'dataMax']} tickFormatter={fmtTick} {...axis}
            label={axisLabel(xName, tokens, { position: 'insideBottom', offset: -10 })} />
          <YAxis type="number" dataKey={yKey} name={yName} domain={[0, 'dataMax']} tickFormatter={fmtTick} {...axis} width={44}
            label={axisLabel(yName, tokens, { angle: -90, position: 'insideLeft', offset: 8 })} />
          <ZAxis range={[14, 14]} />
          <RTooltip cursor={{ strokeDasharray: '3 3', stroke: 'var(--line-strong)' }} content={<MonoTooltip labelFormat={() => 'held-out sample'} />} />
          {ideal && <ReferenceLine segment={[{ x: 0, y: 0 }, { x: ideal, y: ideal }]} ifOverflow="visible" stroke={tokens.alert} strokeDasharray="5 4" strokeWidth={1.4} />}
          <Scatter data={data} fill={tokens[tone]} fillOpacity={0.45} isAnimationActive={false} />
        </ScatterChart>
      )}
    </ChartFrame>
  )
}

function quantile(sorted, q) {
  if (!sorted.length) return 0
  const pos = (sorted.length - 1) * q
  const lo = Math.floor(pos)
  const hi = Math.ceil(pos)
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo)
}

// Box plot drawn in SVG: groups = [{label, color, values[]}] -> median, IQR, whiskers (1.5 IQR), mean marker, outliers.
export function BoxPlot({ groups, height = 280, yName, label }) {
  const ref = useRef(null)
  const { width } = useSize(ref)
  const { tokens } = useChartTheme()
  const m = { l: 46, r: 12, t: 12, b: 28 }
  const stats = groups.map((g) => {
    const v = [...g.values].sort((a, b) => a - b)
    const q1 = quantile(v, 0.25), med = quantile(v, 0.5), q3 = quantile(v, 0.75)
    const iqr = q3 - q1
    const inl = v.filter((x) => x >= q1 - 1.5 * iqr && x <= q3 + 1.5 * iqr)
    return { ...g, n: v.length, q1, med, q3, lo: inl[0] ?? 0, hi: inl[inl.length - 1] ?? 0, mean: v.length ? v.reduce((a, b) => a + b, 0) / v.length : 0, out: v.filter((x) => !inl.includes(x)) }
  })
  const max = Math.max(1, ...stats.flatMap((s) => [s.hi, ...s.out])) * 1.08
  const W = Math.max(width, 10)
  const iw = W - m.l - m.r
  const ih = height - m.t - m.b
  const y = (v) => m.t + ih - (v / max) * ih
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * max)
  const band = iw / Math.max(groups.length, 1)
  return (
    <div ref={ref} style={{ height }} className="w-full" role="figure" aria-label={label}>
      {width > 0 && (
        <svg width={W} height={height}>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke={tokens.grid} />
              <text x={m.l - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fontFamily={MONO} fill={tokens.muted}>{t < 10 ? t.toFixed(1) : Math.round(t)}</text>
            </g>
          ))}
          {yName && <text transform={`translate(10 ${m.t + ih / 2}) rotate(-90)`} textAnchor="middle" fontSize="10" fontFamily={MONO} fill={tokens.dim}>{yName}</text>}
          {stats.map((s, i) => {
            const cx = m.l + band * (i + 0.5)
            const bw = Math.min(54, band * 0.5)
            return (
              <g key={s.label}>
                {s.n > 0 ? (
                  <>
                    <line x1={cx} x2={cx} y1={y(s.lo)} y2={y(s.hi)} stroke={s.color} strokeWidth="1.5" />
                    <line x1={cx - bw / 4} x2={cx + bw / 4} y1={y(s.lo)} y2={y(s.lo)} stroke={s.color} strokeWidth="1.5" />
                    <line x1={cx - bw / 4} x2={cx + bw / 4} y1={y(s.hi)} y2={y(s.hi)} stroke={s.color} strokeWidth="1.5" />
                    <rect x={cx - bw / 2} y={y(s.q3)} width={bw} height={Math.max(2, y(s.q1) - y(s.q3))} fill={s.color} fillOpacity="0.2" stroke={s.color} strokeWidth="1.5" rx="2" />
                    <line x1={cx - bw / 2} x2={cx + bw / 2} y1={y(s.med)} y2={y(s.med)} stroke={s.color} strokeWidth="2.5" />
                    <path d={`M${cx} ${y(s.mean) - 4}l4 4-4 4-4-4z`} fill={tokens.fg} />
                    {s.out.map((o, k) => <circle key={k} cx={cx} cy={y(o)} r="2.5" fill="none" stroke={s.color} />)}
                    <title>{`${s.label}: n=${s.n}, median ${s.med.toFixed(1)}, mean ${s.mean.toFixed(1)}, IQR ${s.q1.toFixed(1)}-${s.q3.toFixed(1)}`}</title>
                  </>
                ) : (
                  <text x={cx} y={y(0) - 8} textAnchor="middle" fontSize="10" fontFamily={MONO} fill={tokens.dim}>no data</text>
                )}
                <text x={cx} y={height - 8} textAnchor="middle" fontSize="10" fontFamily={MONO} fill={tokens.muted}>{s.label}</text>
              </g>
            )
          })}
        </svg>
      )}
    </div>
  )
}

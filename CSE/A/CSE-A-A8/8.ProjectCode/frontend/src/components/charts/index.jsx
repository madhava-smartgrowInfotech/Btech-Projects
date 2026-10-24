import { useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useChartColors } from './colors'
import { Card, CardHeader } from '../ui/display'

export function ChartCard({ title, subtitle, actions, children, height = 280, legend }) {
  return (
    <Card className="chart-card">
      <CardHeader title={title} subtitle={subtitle} actions={actions} />
      <div className="card-body chart-glow">
        {legend}
        <div style={{ width: '100%', height }}>{children}</div>
      </div>
    </Card>
  )
}

export function ChartTooltip({ active, payload, label, valueFormat = (v) => v, labelFormat = (l) => l }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      {label !== undefined && <div className="chart-tooltip-title">{labelFormat(label)}</div>}
      {payload.map((p) => (
        <div key={p.dataKey ?? p.name} className="chart-tooltip-row">
          <span>
            <i style={{ background: p.color || p.payload?.fill }} />
            {p.name}
          </span>
          <strong>{valueFormat(p.value, p)}</strong>
        </div>
      ))}
    </div>
  )
}

export function Legend({ items }) {
  return (
    <div className="legend" style={{ marginBottom: 10 }}>
      {items.map((it) => (
        <span key={it.label}>
          <i style={{ background: it.color }} />
          {it.label}
        </span>
      ))}
    </div>
  )
}

const axis = (c) => ({ stroke: c.grid, tick: { fill: c.text3, fontSize: 12 }, tickLine: false, axisLine: false })

// Grouped bars - one group per category, one bar per series.
export function GroupedBarChart({ data, xKey, series, yDomain = [0, 1], valueFormat, labelFormat }) {
  const c = useChartColors()
  return (
    <ResponsiveContainer>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barGap={4} barCategoryGap="22%">
        <defs>
          {series.map((s, i) => (
            <linearGradient key={s.key} id={`gb-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor={s.color || c.series[i % 4]} stopOpacity={0.95} />
              <stop offset="1" stopColor={s.color || c.series[i % 4]} stopOpacity={0.35} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid vertical={false} stroke={c.grid} />
        <XAxis dataKey={xKey} {...axis(c)} tickFormatter={labelFormat} interval={0} />
        <YAxis domain={yDomain} {...axis(c)} tickFormatter={valueFormat} width={52} />
        <Tooltip cursor={{ fill: c.grid }} content={<ChartTooltip valueFormat={valueFormat} labelFormat={labelFormat} />} />
        {series.map((s, i) => (
          <Bar key={s.key} dataKey={s.key} name={s.label} fill={`url(#gb-${s.key})`} stroke={s.color || c.series[i % 4]} strokeWidth={1} radius={[6, 6, 0, 0]} maxBarSize={34} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

export function HBarChart({ data, labelKey, valueKey, valueFormat = (v) => v, color }) {
  const c = useChartColors()
  const fill = color || c.accent
  return (
    <ResponsiveContainer>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }} barCategoryGap="22%">
        <defs>
          <linearGradient id={`hb-${valueKey}`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={c.accent2} stopOpacity={0.35} />
            <stop offset="1" stopColor={fill} stopOpacity={0.95} />
          </linearGradient>
        </defs>
        <CartesianGrid horizontal={false} stroke={c.grid} />
        <XAxis type="number" {...axis(c)} tickFormatter={valueFormat} />
        <YAxis type="category" dataKey={labelKey} {...axis(c)} width={170} tick={{ fill: c.text2, fontSize: 11.5, fontFamily: 'JetBrains Mono, monospace' }} />
        <Tooltip cursor={{ fill: c.grid }} content={<ChartTooltip valueFormat={valueFormat} />} />
        <Bar dataKey={valueKey} name="Importance" fill={`url(#hb-${valueKey})`} stroke={fill} strokeWidth={1} radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function DonutChart({ data, centerLabel, centerValue }) {
  const c = useChartColors()
  const [active, setActive] = useState(null)
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="62%"
            outerRadius="88%"
            paddingAngle={data.filter((d) => d.value > 0).length > 1 ? 3 : 0}
            stroke={c.panel}
            strokeWidth={2}
            onMouseEnter={(_, i) => setActive(i)}
            onMouseLeave={() => setActive(null)}
          >
            {data.map((d, i) => (
              <Cell key={d.name} fill={d.color} fillOpacity={active === null || active === i ? 1 : 0.4} />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', pointerEvents: 'none', textAlign: 'center' }}>
        <div>
          <div style={{ font: '700 26px/1 var(--font-display)' }}>{centerValue}</div>
          <div className="faint">{centerLabel}</div>
        </div>
      </div>
    </div>
  )
}

export function AreaTrend({ data, xKey, yKey, name, valueFormat = (v) => v, labelFormat = (l) => l, yDomain = ['auto', 'auto'], refLines }) {
  const c = useChartColors()
  return (
    <ResponsiveContainer>
      <AreaChart data={data} margin={{ top: 10, right: 8, left: -12, bottom: 0 }}>
        <defs>
          <linearGradient id={`at-${yKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={c.accent} stopOpacity={0.35} />
            <stop offset="1" stopColor={c.accent} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke={c.grid} />
        <XAxis dataKey={xKey} {...axis(c)} tickFormatter={labelFormat} minTickGap={24} />
        <YAxis {...axis(c)} domain={yDomain} tickFormatter={valueFormat} width={52} />
        <Tooltip content={<ChartTooltip valueFormat={valueFormat} labelFormat={labelFormat} />} cursor={{ stroke: c.accent, strokeOpacity: 0.4 }} />
        {refLines}
        <Area
          type="monotone"
          dataKey={yKey}
          name={name}
          stroke={c.accent}
          strokeWidth={2.2}
          fill={`url(#at-${yKey})`}
          dot={false}
          activeDot={{ r: 5, fill: c.accent, stroke: c.panel, strokeWidth: 2 }}
          className="recharts-line-curve"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function RadarCompare({ data, series, angleKey }) {
  const c = useChartColors()
  return (
    <ResponsiveContainer>
      <RadarChart data={data} outerRadius="66%" margin={{ top: 8, right: 28, bottom: 8, left: 28 }}>
        <PolarGrid stroke={c.grid} />
        <PolarAngleAxis dataKey={angleKey} tick={{ fill: c.text2, fontSize: 12 }} />
        <Tooltip content={<ChartTooltip valueFormat={(v) => `${(v * 100).toFixed(1)}%`} />} />
        {series.map((s, i) => (
          <Radar key={s.key} dataKey={s.key} name={s.label} stroke={s.color || c.series[i % 4]} fill={s.color || c.series[i % 4]} fillOpacity={0.12} strokeWidth={2} />
        ))}
      </RadarChart>
    </ResponsiveContainer>
  )
}


// Result over time with the reference range drawn as a shaded band (or a limit line for one-sided ranges).
// Dots take the colour of each point's status so abnormal values stand out.
export function TrendChart({ data, name, unit, valueFormat = (v) => v, labelFormat = (l) => l }) {
  const c = useChartColors()
  const lows = data.map((d) => d.low).filter((v) => v !== null && v !== undefined)
  const highs = data.map((d) => d.high).filter((v) => v !== null && v !== undefined)
  const low = lows.length ? lows[lows.length - 1] : null
  const high = highs.length ? highs[highs.length - 1] : null
  const values = data.map((d) => d.value).filter((v) => v !== null && v !== undefined)
  const all = [...values, ...(low !== null ? [low] : []), ...(high !== null ? [high] : [])]
  const min = Math.min(...all)
  const max = Math.max(...all)
  const pad = (max - min || Math.abs(max) || 1) * 0.15
  const raw = (max + pad - (min - pad)) / 4
  const pow = 10 ** Math.floor(Math.log10(raw))
  const step = (raw / pow <= 1 ? 1 : raw / pow <= 2 ? 2 : raw / pow <= 5 ? 5 : 10) * pow
  const lo = Math.floor((min - pad) / step) * step
  const hi = Math.ceil((max + pad) / step) * step
  const ticks = []
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(Number(v.toFixed(6)))
  const tone = { LOW: c.warn, HIGH: c.danger, NORMAL: c.accent, UNKNOWN: c.text3 }
  const Dot = ({ cx, cy, payload }) =>
    cx === undefined || cy === undefined ? null : <circle cx={cx} cy={cy} r={5} fill={tone[payload.status] || c.accent} stroke={c.panel} strokeWidth={2} />
  return (
    <ResponsiveContainer>
      <LineChart data={data} margin={{ top: 10, right: 12, left: -6, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={c.grid} />
        <XAxis dataKey="date" {...axis(c)} tickFormatter={labelFormat} minTickGap={24} />
        <YAxis {...axis(c)} domain={[lo, hi]} ticks={ticks} tickFormatter={valueFormat} width={56} />
        <Tooltip content={<ChartTooltip valueFormat={(v) => `${valueFormat(v)}${unit ? ` ${unit}` : ''}`} labelFormat={labelFormat} />} cursor={{ stroke: c.accent, strokeOpacity: 0.4 }} />
        {low !== null && high !== null && <ReferenceArea y1={low} y2={high} fill={c.accent} fillOpacity={0.1} stroke={c.accent} strokeOpacity={0.35} strokeDasharray="4 4" ifOverflow="extendDomain" />}
        {low !== null && high === null && <ReferenceLine y={low} stroke={c.warn} strokeDasharray="4 4" ifOverflow="extendDomain" label={{ value: `min ${valueFormat(low)}`, fill: c.text3, fontSize: 11, position: 'insideBottomRight' }} />}
        {high !== null && low === null && <ReferenceLine y={high} stroke={c.danger} strokeDasharray="4 4" ifOverflow="extendDomain" label={{ value: `max ${valueFormat(high)}`, fill: c.text3, fontSize: 11, position: 'insideTopRight' }} />}
        <Line type="monotone" dataKey="value" name={name} stroke={c.accent} strokeWidth={2.4} dot={<Dot />} activeDot={{ r: 7, stroke: c.panel, strokeWidth: 2 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

export { useChartColors }

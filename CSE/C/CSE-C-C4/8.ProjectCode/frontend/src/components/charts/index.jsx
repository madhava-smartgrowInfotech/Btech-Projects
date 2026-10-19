// Recharts wrappers themed for Soft Pastel Calm: rounded bars, pastel fills, soft tooltips.
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useId } from 'react'
import { useReducedMotion } from 'framer-motion'
import { PASTEL, useChartTheme } from '../../lib/palette'

export function PastelTooltip({ active, payload, label, valueFormat = (v) => v, labelFormat = (l) => l }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tip">
      <div className="chart-tip-title">{labelFormat(label, payload)}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="chart-tip-row">
          <span>
            <i className="chart-tip-sw" style={{ background: p.color || p.payload?.fill }} />
            {p.name}
          </span>
          <b>{valueFormat(p.value, p.dataKey)}</b>
        </div>
      ))}
    </div>
  )
}

export function ChartLegend({ items }) {
  return (
    <div className="legend" aria-hidden="true">
      {items.map((i) => (
        <span key={i.label}>
          <i style={{ background: i.color }} />
          {i.label}
        </span>
      ))}
    </div>
  )
}

function useAxis() {
  const t = useChartTheme()
  return {
    t,
    axis: { stroke: t.axis, fontSize: 12, tickLine: false, axisLine: false, tick: { fill: t.axis } },
    grid: <CartesianGrid stroke={t.grid} strokeDasharray="4 6" vertical={false} />,
  }
}

const anim = (reduce) => ({ isAnimationActive: !reduce, animationDuration: 900, animationEasing: 'ease-out' })

/** Single-series area trend. data: [{x, y}] */
export function AreaTrend({ data, color, valueFormat, xFormat, yFormat, height = 300, name = 'Value', label }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  const c = color || t.lavender
  const gid = `area${useId().replace(/:/g, '')}`
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor={c} stopOpacity={0.55} />
              <stop offset="1" stopColor={c} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          {grid}
          <XAxis dataKey="x" {...axis} tickFormatter={xFormat} minTickGap={24} />
          <YAxis {...axis} tickFormatter={yFormat} width={52} />
          <Tooltip cursor={{ stroke: t.lavender, strokeWidth: 2, strokeDasharray: '4 4' }} content={<PastelTooltip valueFormat={valueFormat} labelFormat={xFormat} />} />
          <Area type="monotone" dataKey="y" name={name} stroke={c} strokeWidth={3} fill={`url(#${gid})`} activeDot={{ r: 6, strokeWidth: 3, stroke: t.surface }} {...anim(reduce)} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Rounded bars. data: [{name, value, highlight}] ; horizontal for long labels.
 */
export function BarCompare({ data, valueFormat = (v) => v, height = 300, horizontal = false, color, highlightColor, name = 'Value', label, yWidth = 150 }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  const base = color || t.sky
  const hi = highlightColor || t.lavender
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        {horizontal ? (
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 4 }} barCategoryGap="22%">
            <CartesianGrid stroke={t.grid} strokeDasharray="4 6" horizontal={false} />
            <XAxis type="number" {...axis} tickFormatter={valueFormat} />
            <YAxis type="category" dataKey="name" {...axis} width={yWidth} tick={{ fill: t.text, fontSize: 12.5 }} />
            <Tooltip cursor={{ fill: t.cursor, radius: 12 }} content={<PastelTooltip valueFormat={valueFormat} />} />
            <Bar dataKey="value" name={name} radius={[0, 12, 12, 0]} {...anim(reduce)}>
              {data.map((d) => (
                <Cell key={d.name} fill={d.color || (d.highlight ? hi : base)} />
              ))}
            </Bar>
          </BarChart>
        ) : (
          <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }} barCategoryGap="24%">
            {grid}
            <XAxis dataKey="name" {...axis} interval={0} tick={{ fill: t.axis, fontSize: 11.5 }} />
            <YAxis {...axis} tickFormatter={valueFormat} width={56} />
            <Tooltip cursor={{ fill: t.cursor, radius: 12 }} content={<PastelTooltip valueFormat={valueFormat} />} />
            <Bar dataKey="value" name={name} radius={[12, 12, 12, 12]} {...anim(reduce)}>
              {data.map((d) => (
                <Cell key={d.name} fill={d.color || (d.highlight ? hi : base)} />
              ))}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}

/** Multi-series lines. series: [{key, name, color, dashed}] data: [{x, ...}] */
export function LineCompare({ data, series, valueFormat = (v) => v, xFormat, yFormat, height = 300, label, domain, dots = true }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          {grid}
          <XAxis dataKey="x" {...axis} tickFormatter={xFormat} minTickGap={16} />
          <YAxis {...axis} tickFormatter={yFormat || valueFormat} width={56} domain={domain || ['auto', 'auto']} />
          <Tooltip cursor={{ stroke: t.lavender, strokeWidth: 2, strokeDasharray: '4 4' }} content={<PastelTooltip valueFormat={valueFormat} labelFormat={xFormat} />} />
          {series.map((s, i) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color || PASTEL[i]}
              strokeWidth={3.2}
              strokeDasharray={s.dashed ? '6 6' : undefined}
              dot={dots ? { r: 4, strokeWidth: 2.5, fill: t.surface } : false}
              activeDot={{ r: 7, strokeWidth: 3, stroke: t.surface }}
              {...anim(reduce)}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Grouped rounded bars. series: [{key, name, color}] data: [{x, ...}] */
export function GroupedBars({ data, series, valueFormat = (v) => v, xFormat, height = 300, label }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }} barGap={6} barCategoryGap="26%">
          {grid}
          <XAxis dataKey="x" {...axis} tickFormatter={xFormat} />
          <YAxis {...axis} tickFormatter={valueFormat} width={56} />
          <Tooltip cursor={{ fill: t.cursor, radius: 12 }} content={<PastelTooltip valueFormat={valueFormat} labelFormat={xFormat} />} />
          {series.map((s, i) => (
            <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color || PASTEL[i]} radius={[10, 10, 10, 10]} {...anim(reduce)} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Price history + dashed forecast + shaded confidence band.
 * data: [{x, close?, forecast?, band?: [lower, upper]}] ; splitAt: x of the last actual close.
 */
export function ForecastChart({ data, valueFormat = (v) => v, xFormat, height = 360, label, splitAt }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  const gid = `band${useId().replace(/:/g, '')}`
  const tip = ({ active, payload, label: l }) => {
    if (!active || !payload?.length) return null
    const row = payload[0].payload
    return (
      <div className="chart-tip">
        <div className="chart-tip-title">{xFormat ? xFormat(l, true) : l}</div>
        {row.close != null && (
          <div className="chart-tip-row">
            <span>
              <i className="chart-tip-sw" style={{ background: t.text }} />
              Actual close
            </span>
            <b>{valueFormat(row.close)}</b>
          </div>
        )}
        {row.forecast != null && row.band && (
          <>
            <div className="chart-tip-row">
              <span>
                <i className="chart-tip-sw" style={{ background: t.lavender }} />
                Forecast
              </span>
              <b>{valueFormat(row.forecast)}</b>
            </div>
            <div className="chart-tip-row">
              <span>
                <i className="chart-tip-sw" style={{ background: t.sky }} />
                Band
              </span>
              <b>
                {valueFormat(row.band[0])} – {valueFormat(row.band[1])}
              </b>
            </div>
          </>
        )}
      </div>
    )
  }
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor={t.lavender} stopOpacity={0.4} />
              <stop offset="1" stopColor={t.sky} stopOpacity={0.25} />
            </linearGradient>
          </defs>
          {grid}
          <XAxis dataKey="x" {...axis} tickFormatter={(v) => (xFormat ? xFormat(v) : v)} minTickGap={32} />
          <YAxis {...axis} tickFormatter={valueFormat} width={64} domain={['auto', 'auto']} />
          <Tooltip cursor={{ stroke: t.lavender, strokeWidth: 2, strokeDasharray: '4 4' }} content={tip} />
          {splitAt && <ReferenceLine x={splitAt} stroke={t.axis} strokeDasharray="3 5" />}
          <Area type="monotone" dataKey="band" name="Confidence band" stroke="none" fill={`url(#${gid})`} connectNulls {...anim(reduce)} />
          <Line type="monotone" dataKey="close" name="Actual close" stroke={t.text} strokeWidth={2.6} dot={false} activeDot={{ r: 5, strokeWidth: 3, stroke: t.surface }} {...anim(reduce)} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke={t.lavender} strokeWidth={3.2} strokeDasharray="7 6" dot={false} activeDot={{ r: 6, strokeWidth: 3, stroke: t.surface }} connectNulls {...anim(reduce)} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Bars + line on one axis (e.g. realised vs forecast). */
export function BarLine({ data, bar, line, valueFormat = (v) => v, xFormat, height = 300, label }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }} barCategoryGap="28%">
          {grid}
          <XAxis dataKey="x" {...axis} tickFormatter={xFormat} />
          <YAxis {...axis} tickFormatter={valueFormat} width={56} />
          <Tooltip cursor={{ fill: t.cursor, radius: 12 }} content={<PastelTooltip valueFormat={valueFormat} labelFormat={xFormat} />} />
          <Bar dataKey={bar.key} name={bar.name} fill={bar.color || t.sky} radius={[12, 12, 12, 12]} {...anim(reduce)} />
          <Line type="monotone" dataKey={line.key} name={line.name} stroke={line.color || t.peach} strokeWidth={3.2} dot={{ r: 4.5, strokeWidth: 2.5, fill: t.surface }} {...anim(reduce)} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

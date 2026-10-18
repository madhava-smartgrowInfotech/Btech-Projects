// Project-specific chart wrappers (donut, ROC/PR curves, overlaid areas) in the same pastel style as the kit.
import { useId } from 'react'
import { useReducedMotion } from 'framer-motion'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { PASTEL, useChartTheme } from '../../lib/palette'
import { ChartLegend, PastelTooltip } from './index'

const anim = (reduce) => ({ isAnimationActive: !reduce, animationDuration: 900, animationEasing: 'ease-out' })

function useAxis() {
  const t = useChartTheme()
  return {
    t,
    axis: { stroke: t.axis, fontSize: 12, tickLine: false, axisLine: false, tick: { fill: t.axis } },
    grid: <CartesianGrid stroke={t.grid} strokeDasharray="4 6" vertical={false} />,
  }
}

/** Donut with a centre label. data: [{name, value, color}] */
export function DonutChart({ data, height = 260, centerValue, centerLabel, label, valueFormat = (v) => v.toLocaleString('en-IN') }) {
  useAxis()
  const reduce = useReducedMotion()
  const total = data.reduce((s, d) => s + d.value, 0)
  return (
    <div>
    <div className="chart-box donut" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <PieChart>
          <Tooltip content={<PastelTooltip valueFormat={valueFormat} labelFormat={(_, p) => p?.[0]?.name} />} />
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="62%"
            outerRadius="88%"
            paddingAngle={3}
            cornerRadius={10}
            stroke="none"
            {...anim(reduce)}
          >
            {data.map((d, i) => (
              <Cell key={d.name} fill={d.color || PASTEL[i % PASTEL.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      {centerValue != null && (
        <div className="donut-center" aria-hidden="true">
          <b>{centerValue}</b>
          <span>{centerLabel || `${total.toLocaleString('en-IN')} total`}</span>
        </div>
      )}
    </div>
    <ChartLegend items={data.map((d, i) => ({ label: `${d.name} (${valueFormat(d.value)})`, color: d.color || PASTEL[i % PASTEL.length] }))} />
    </div>
  )
}

/** Numeric-x lines, each series with its own points (ROC / precision-recall). series: [{key, name, color, data:[{x,y}], dashed}] */
export function CurvesChart({ series, xLabel, height = 320, label, valueFormat = (v) => v.toFixed(2) }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  return (
    <div>
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <LineChart margin={{ top: 10, right: 12, left: 0, bottom: 22 }}>
          {grid}
          <XAxis
            type="number"
            dataKey="x"
            domain={[0, 1]}
            {...axis}
            tickFormatter={valueFormat}
            label={{ value: xLabel, position: 'insideBottom', offset: -14, fill: t.axis, fontSize: 12 }}
          />
          <YAxis
            type="number"
            domain={[0, 1]}
            {...axis}
            tickFormatter={valueFormat}
            width={58}
          />
          <Tooltip cursor={{ stroke: t.lavender, strokeWidth: 2, strokeDasharray: '4 4' }} content={<PastelTooltip valueFormat={valueFormat} labelFormat={(l) => `${xLabel}: ${valueFormat(l)}`} />} />
          {series.map((s, i) => (
            <Line
              key={s.key}
              data={s.data}
              dataKey="y"
              name={s.name}
              type="linear"
              stroke={s.color || PASTEL[i % PASTEL.length]}
              strokeWidth={s.dashed ? 2 : 3.2}
              strokeDasharray={s.dashed ? '6 6' : undefined}
              dot={false}
              activeDot={s.dashed ? false : { r: 6, strokeWidth: 3, stroke: t.surface }}
              legendType={s.dashed ? 'plainline' : 'circle'}
              {...anim(reduce)}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
    <ChartLegend items={series.map((s, i) => ({ label: s.name, color: s.color || PASTEL[i % PASTEL.length] }))} />
    </div>
  )
}

/** Two overlaid areas on one numeric axis (distribution of a feature by churn). series: [{key, name, color}] data: [{x, ...}] */
export function OverlayArea({ data, series, height = 300, label, xFormat, valueFormat = (v) => v.toLocaleString('en-IN') }) {
  const { t, axis, grid } = useAxis()
  const reduce = useReducedMotion()
  const gid = `ov${useId().replace(/:/g, '')}`
  return (
    <div>
    <div className="chart-box" style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
          <defs>
            {series.map((s, i) => (
              <linearGradient key={s.key} id={`${gid}${i}`} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0" stopColor={s.color} stopOpacity={0.6} />
                <stop offset="1" stopColor={s.color} stopOpacity={0.05} />
              </linearGradient>
            ))}
          </defs>
          {grid}
          <XAxis dataKey="x" {...axis} tickFormatter={xFormat} minTickGap={28} />
          <YAxis {...axis} width={44} />
          <Tooltip cursor={{ stroke: t.lavender, strokeWidth: 2, strokeDasharray: '4 4' }} content={<PastelTooltip valueFormat={valueFormat} labelFormat={(l) => `${xFormat ? xFormat(l) : l}`} />} />
          {series.map((s, i) => (
            <Area key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={3} fill={`url(#${gid}${i})`} {...anim(reduce)} />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
    <ChartLegend items={series.map((s) => ({ label: s.name, color: s.color }))} />
    </div>
  )
}

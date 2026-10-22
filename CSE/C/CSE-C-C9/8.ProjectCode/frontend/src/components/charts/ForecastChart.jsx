import { useMemo } from 'react'
import { useReducedMotion } from 'framer-motion'
import { Area, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts'
import { useChartTheme } from '../../lib/palette'
import { monthLabel, fmtNum } from '../../lib/format'
import { PastelTooltip } from './index'

/** History + forecast line with the 95% interval band. Uses only values the API returned. */
export default function ForecastChart({ history = [], forecast = [], height = 360, sinceYear, label }) {
  const t = useChartTheme()
  const reduce = useReducedMotion()
  const data = useMemo(() => {
    const h = sinceYear ? history.filter((d) => Number(d.date.slice(0, 4)) >= sinceYear) : history
    const rows = h.map((d) => ({ x: d.date, history: d.value }))
    const last = rows[rows.length - 1]
    // anchor the forecast line on the last observed point so the two lines join
    if (last) last.forecast = last.history
    forecast.forEach((d) =>
      rows.push({ x: d.date, forecast: d.value, lower: d.lower, band: +(d.upper - d.lower).toFixed(4), upper: d.upper }),
    )
    return rows
  }, [history, forecast, sinceYear])
  // one tick per January (thinned for long histories) so year labels never repeat
  const { ticks, domain, yTicks } = useMemo(() => {
    const jans = data.filter((d) => d.x.endsWith('-01')).map((d) => d.x)
    const step = Math.ceil(jans.length / 6) || 1
    const vals = data.flatMap((d) => [d.history, d.lower, d.upper, d.forecast]).filter((v) => v != null)
    const lo = Math.min(...vals)
    const hi = Math.max(...vals)
    const unit = (hi - lo) / 4 > 7.5 ? 10 : 5
    const min = Math.floor(lo / unit) * unit
    const max = Math.ceil(hi / unit) * unit
    const yTicks = []
    for (let v = min; v <= max; v += unit) yTicks.push(v)
    return { ticks: jans.filter((_, i) => i % step === 0), domain: [min, max], yTicks }
  }, [data])
  const axis = { stroke: t.axis, fontSize: 12, tickLine: false, axisLine: false, tick: { fill: t.axis } }
  const anim = { isAnimationActive: !reduce, animationDuration: 900 }
  const fmt = (v, key) => (key === 'band' ? `± ${fmtNum(v / 2, 2)}` : fmtNum(v, 2))
  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={label || 'Index history and 12-month forecast with 95% interval'}>
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={t.grid} strokeDasharray="4 6" vertical={false} />
          <XAxis dataKey="x" {...axis} ticks={ticks} tickFormatter={(v) => v.slice(0, 4)} />
          <YAxis {...axis} width={48} domain={domain} ticks={yTicks} allowDataOverflow tickFormatter={(v) => Math.round(v)} />
          <Tooltip cursor={{ stroke: t.lavender, strokeWidth: 2, strokeDasharray: '4 4' }} content={<PastelTooltip valueFormat={fmt} labelFormat={(l) => monthLabel(l, true)} />} />
          <Area dataKey="lower" stackId="b" stroke="none" fill="transparent" legendType="none" tooltipType="none" activeDot={false} {...anim} />
          <Area dataKey="band" name="95% interval width" stackId="b" stroke="none" fill={t.mint} fillOpacity={0.4} activeDot={false} {...anim} />
          <Line type="monotone" dataKey="history" name="History" stroke={t.lavender} strokeWidth={3} dot={false} activeDot={{ r: 6, strokeWidth: 3, stroke: t.surface }} {...anim} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke={t.mint} strokeWidth={3.2} strokeDasharray="6 5" dot={false} activeDot={{ r: 6, strokeWidth: 3, stroke: t.surface }} {...anim} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

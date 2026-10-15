import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartTooltip, useChartColors } from './index'

// Multi-series line chart in the kit's chart style (the kit ships an area trend for a single series only).
export function MultiLine({ data, xKey, series, yDomain = [0, 100], valueFormat = (v) => v, labelFormat = (l) => l }) {
  const c = useChartColors()
  const axis = { stroke: c.grid, tick: { fill: c.text3, fontSize: 12 }, tickLine: false, axisLine: false }
  return (
    <ResponsiveContainer>
      <LineChart data={data} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={c.grid} />
        <XAxis dataKey={xKey} {...axis} tickFormatter={labelFormat} minTickGap={28} />
        <YAxis {...axis} domain={yDomain} width={44} />
        <Tooltip content={<ChartTooltip valueFormat={valueFormat} labelFormat={labelFormat} />} cursor={{ stroke: c.accent, strokeOpacity: 0.4 }} />
        {series.map((s, i) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color || c.series[i % 4]}
            strokeWidth={2.2}
            dot={{ r: 3, fill: s.color || c.series[i % 4], strokeWidth: 0 }}
            activeDot={{ r: 5, stroke: c.panel, strokeWidth: 2 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

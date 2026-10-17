/* Live two-series trace in the same flat Neo Brutal chart style as Charts.jsx. */
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BrutalTip, useChartTheme } from './Charts'

/** Twin-axis line chart. series: [{key, name, color, unit}] - first on the left axis, second on the right. */
export function LineTrace({ data, xKey, series, height = 260 }) {
  const { fg, grid, narrow } = useChartTheme()
  const tick = { fill: fg, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fontWeight: 600 }
  const [a, b] = series
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="chart-box" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 12, right: 4, left: -8, bottom: 4 }}>
            <CartesianGrid stroke={grid} strokeDasharray="2 4" vertical={false} />
            <XAxis dataKey={xKey} stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} minTickGap={narrow ? 56 : 36} />
            <YAxis yAxisId="l" stroke={fg} strokeWidth={3} tick={tick} width={40} />
            <YAxis yAxisId="r" orientation="right" stroke={fg} strokeWidth={3} tick={tick} width={36} />
            <Tooltip content={<BrutalTip />} cursor={{ stroke: fg, strokeWidth: 2 }} />
            <Line yAxisId="l" type="linear" dataKey={a.key} name={a.name} stroke={a.color} strokeWidth={4} dot={false} isAnimationActive={false} />
            <Line yAxisId="r" type="linear" dataKey={b.key} name={b.name} stroke={b.color} strokeWidth={4} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="legend" aria-hidden="true">
        {series.map((s) => (
          <span key={s.key}>
            <i style={{ background: s.color }} />
            {s.name}
            {s.unit ? ` (${s.unit})` : ''}
          </span>
        ))}
      </div>
    </div>
  )
}

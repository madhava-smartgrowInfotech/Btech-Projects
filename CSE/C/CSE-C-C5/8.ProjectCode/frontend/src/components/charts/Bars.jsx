import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis, Tooltip as RTooltip } from 'recharts'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../ui/charts'

/**
 * Grouped/single bar chart in the Kinetic Mono style.
 * series: [{ key, label, tone }]  ·  data: [{ [xKey]: label, [series.key]: value }]
 * highlight: x value whose bars are drawn full-strength (others dimmed) - used to pick out the hybrid model.
 */
export function MonoBars({ data, xKey, series, height = 260, domain = [0, 1], valueFormat = (v) => v, highlight, label, layout = 'horizontal', xTickFormat, angle = 0 }) {
  const { tokens, animate, axis, grid } = useChartTheme()
  const vertical = layout === 'vertical'
  return (
    <>
      <ChartFrame height={height} label={label}>
        {({ width, height: h }) => (
          <BarChart width={width} height={h} data={data} layout={layout} margin={{ top: 8, right: 8, bottom: angle ? 34 : 4, left: vertical ? 8 : -12 }} barCategoryGap="22%">
            <CartesianGrid {...grid} vertical={vertical} horizontal={!vertical} />
            {vertical ? (
              <>
                <XAxis type="number" domain={domain} {...axis} allowDecimals />
                <YAxis type="category" dataKey={xKey} width={110} {...axis} interval={0} />
              </>
            ) : (
              <>
                <XAxis dataKey={xKey} {...axis} interval={0} angle={angle} textAnchor={angle ? 'end' : 'middle'} tickFormatter={xTickFormat} height={angle ? 56 : 30} />
                <YAxis domain={domain} {...axis} allowDecimals tickFormatter={valueFormat} />
              </>
            )}
            <RTooltip cursor={{ fill: tokens.line }} content={<MonoTooltip valueFormat={valueFormat} />} />
            {series.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.label} fill={tokens[s.tone] || tokens.ok} isAnimationActive={animate} animationDuration={900} radius={[2, 2, 0, 0]}>
                {highlight !== undefined && data.map((d) => (
                  <Cell key={d[xKey]} fill={tokens[s.tone] || tokens.ok} fillOpacity={d[xKey] === highlight ? 1 : 0.45} />
                ))}
              </Bar>
            ))}
          </BarChart>
        )}
      </ChartFrame>
      {series.length > 1 && <ChartLegend items={series.map((s) => ({ label: s.label, color: tokens[s.tone] || tokens.ok }))} />}
    </>
  )
}

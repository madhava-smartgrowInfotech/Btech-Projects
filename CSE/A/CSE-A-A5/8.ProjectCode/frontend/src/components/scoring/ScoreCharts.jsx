import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, Tooltip as RTooltip, XAxis, YAxis } from 'recharts'
import { useScored } from '../../lib/session'
import { Card } from '../ui/display'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../ui/charts'
import { EmptyState } from '../ui/feedback'
import { PieChart as PieIcon } from 'lucide-react'

const BINS = [['<50%', 0, 0.5], ['50-70%', 0.5, 0.7], ['70-85%', 0.7, 0.85], ['85-100%', 0.85, 1.01]]

export default function ScoreCharts() {
  const log = useScored()
  const { tokens, animate, axis, grid } = useChartTheme()
  const counts = useMemo(() => {
    const a = log.filter((e) => e.label === 'attack').length
    return [{ name: 'Attack', value: a, color: tokens.alert }, { name: 'Normal', value: log.length - a, color: tokens.ok }]
  }, [log, tokens])
  const hist = useMemo(() => BINS.map(([name, lo, hi]) => ({ name, count: log.filter((e) => e.confidence >= lo && e.confidence < hi).length })), [log])
  const empty = <EmptyState icon={PieIcon} title="Charts fill as you score" body="Score a record or a batch to see the split and the confidence spread." className="py-6" />

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <Card title="Attack vs normal" eyebrow="session">
        {log.length === 0 ? empty : (
          <>
            <ChartFrame height={220} crosshair={false} label="Donut chart of attack versus normal records">
              {({ width, height }) => (
                <PieChart width={width} height={height}>
                  <Pie data={counts} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2} stroke="none" isAnimationActive={animate}>
                    {counts.map((c) => <Cell key={c.name} fill={c.color} />)}
                  </Pie>
                  <RTooltip content={<MonoTooltip />} />
                </PieChart>
              )}
            </ChartFrame>
            <ChartLegend items={counts.map((c) => ({ label: `${c.name} ${c.value}`, color: c.color }))} />
          </>
        )}
      </Card>
      <Card title="Confidence distribution" eyebrow="session">
        {log.length === 0 ? empty : (
          <>
            <ChartFrame height={220} label="Bar chart of ensemble confidence buckets">
              {({ width, height }) => (
                <BarChart width={width} height={height} data={hist} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                  <CartesianGrid vertical={false} {...grid} />
                  <XAxis dataKey="name" {...axis} />
                  <YAxis allowDecimals={false} {...axis} />
                  <RTooltip cursor={{ fill: tokens.line }} content={<MonoTooltip />} />
                  <Bar dataKey="count" name="Records" fill={tokens.cyan} radius={[2, 2, 0, 0]} isAnimationActive={animate} />
                </BarChart>
              )}
            </ChartFrame>
            <ChartLegend items={[{ label: 'Records per ensemble-confidence bucket', color: tokens.cyan }]} />
          </>
        )}
      </Card>
    </div>
  )
}

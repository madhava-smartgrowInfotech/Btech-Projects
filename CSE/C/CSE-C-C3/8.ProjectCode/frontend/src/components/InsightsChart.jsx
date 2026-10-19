import { ChartCard, GroupedBarChart, Legend, useChartColors } from './charts'
import { STRATEGY_LABEL } from '../lib/format'

// Totals per buffer strategy as grouped bars: unable-to-park vs declined.
export default function InsightsChart({ totals, height = 300, actions }) {
  const c = useChartColors()
  const data = Object.keys(STRATEGY_LABEL).map((k) => ({
    name: STRATEGY_LABEL[k],
    unable: totals[k]?.unable_to_park ?? 0,
    declined: totals[k]?.declined ?? 0,
  }))
  const series = [
    { key: 'unable', label: 'Unable to park', color: c.danger },
    { key: 'declined', label: 'Declined', color: c.warn },
  ]
  return (
    <ChartCard
      title="Buffer strategy comparison"
      subtitle="Same booking history replayed under four buffer policies - lower is better"
      height={height}
      actions={actions}
      legend={<Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
    >
      <GroupedBarChart data={data} xKey="name" series={series} yDomain={[0, 'auto']} />
    </ChartCard>
  )
}

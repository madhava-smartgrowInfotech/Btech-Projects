import { LineChart as LineIcon } from 'lucide-react'
import { ChartCard, Legend } from '../charts'
import { useSimulation } from '../../hooks/useSimulation'
import { Button } from '../ui/controls'
import { EmptyState, Skeleton } from '../ui/feedback'

/** Chart card with the three states every chart needs: loading skeleton, empty-with-action, and the chart itself. */
export default function ChartPanel({ title, subtitle, legend, height = 260, hasData, children, actions, cta = false }) {
  const { ready, series, step, busy, status } = useSimulation()
  const finished = !!status && status.step >= status.total_steps
  let body = children
  let h = height
  if (!ready) body = <Skeleton height={height - 20} radius={12} />
  else if (!hasData && !series.length) {
    h = 'auto'
    body = (
      <EmptyState icon={LineIcon} title="No data to plot yet" actions={cta ? <Button variant="primary" disabled={!!busy || finished} loading={busy === 'advance one step'} onClick={step}>Run one step</Button> : undefined}>
        Charts fill in as the simulation advances. Use the run controls above to step or start the simulation.
      </EmptyState>
    )
  }
  return (
    <ChartCard title={title} subtitle={subtitle} height={h} legend={ready && series.length ? legend && <Legend items={legend} /> : null} actions={actions}>
      {body}
    </ChartCard>
  )
}

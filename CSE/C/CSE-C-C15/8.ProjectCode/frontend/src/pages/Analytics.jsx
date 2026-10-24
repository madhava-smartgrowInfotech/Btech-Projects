import { BarChart3 } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ConfidenceChart, PredictionDonut, ProtocolBars, RateChart, SeverityBars } from '../components/app/Charts'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton } from '../components/ui/feedback'
import { fmt } from '../format'
import { useLive } from '../lib/live'

export default function Analytics() {
  const { loaded, error, refresh, detections, byPrediction, bySeverity } = useLive()
  const series = useMemo(() => detections.slice(0, 60).reverse().map((d) => ({
    t: d.timestamp, rate: d.packet_rate, attack: d.prediction === 'Attack', confidence: d.confidence, risk: d.distributed_risk,
  })), [detections])
  const proto = useMemo(() => {
    const p = detections[0]?.detail?.context?.protocol_distribution || {}
    return Object.entries(p).map(([name, value]) => ({ name, value }))
  }, [detections])

  if (!loaded) return <PageSkeleton />
  const benign = byPrediction.Benign || 0
  const attack = byPrediction.Attack || 0
  const total = benign + attack

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="console / analytics" title="Detection analytics"
        subtitle="Totals come from every stored detection; the timelines show the most recent windows." />
      {error && <ErrorState error={error} title="Backend unreachable" onRetry={refresh} />}
      {total === 0 ? (
        <Card title="Analytics">
          <EmptyState icon={BarChart3} title="Nothing to chart yet" body="Analytics fill in once a session has scored some windows."
            action={<Link to="/app"><Button>Go to session control</Button></Link>} />
        </Card>
      ) : (
        <>
          <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard label="Windows scored" value={total} />
            <StatCard label="Attack windows" tone="alert" value={attack} sub={`${((attack / total) * 100).toFixed(1)}% of all windows`} />
            <StatCard label="Benign windows" value={benign} sub={`${((benign / total) * 100).toFixed(1)}% of all windows`} />
            <StatCard label="High + critical" tone="hot" value={(bySeverity.High || 0) + (bySeverity.Critical || 0)} sub="windows that triggered quarantine" />
          </Stagger>
          <div className="grid gap-5 lg:grid-cols-2">
            <Card title="Benign vs attack"><PredictionDonut benign={benign} attack={attack} /></Card>
            <Card title="Severity distribution"><SeverityBars counts={bySeverity} /></Card>
          </div>
          <Card title="Packet rate timeline" action={<span className="font-mono text-[11px] text-dim">last {series.length} windows</span>}><RateChart rows={series} /></Card>
          <div className="grid gap-5 lg:grid-cols-2">
            <Card title="Confidence and distributed risk"><ConfidenceChart rows={series} /></Card>
            <Card title="Protocol mix · latest window"
              action={detections[0] && <span className="font-mono text-[11px] text-dim">{fmt(detections[0].detail?.context?.packet_count)} packets</span>}>
              {proto.length ? <ProtocolBars data={proto} /> : <EmptyState title="No protocol data" body="The latest window did not record a protocol breakdown." />}
            </Card>
          </div>
        </>
      )}
    </div>
  )
}

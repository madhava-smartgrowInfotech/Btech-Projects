import { Eye, Gauge, Play, ShieldAlert, Siren, Ticket } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { describeError } from '../api'
import { VEHICLE } from '../format'
import { logEvent } from '../lib/activity'
import { useLive } from '../lib/live'
import { useGet } from '../lib/useRequest'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge, Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { BarsChart } from '../components/ui/chartsMore'

const COLUMNS = [
  { key: 'time', label: 'Time', render: (r) => <span className="font-mono tabular-nums text-muted">{r.time}</span> },
  { key: 'junction', label: 'Junction', sortable: true, render: (r) => <span className="font-mono">{r.junction}</span> },
  { key: 'approach', label: 'Approach', render: (r) => <span className="font-mono">{r.approach}</span> },
  { key: 'kind', label: 'Violation', sortable: true, render: (r) => <Badge tone={r.kind.startsWith('Red') ? 'alert' : 'warn'}>{r.kind}</Badge> },
  { key: 'plate', label: 'Plate', render: (r) => <span className="font-mono text-fg">{r.plate}</span> },
  { key: 'vehicle', label: 'Vehicle', render: (r) => <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-2 rounded-[2px]" style={{ background: (VEHICLE[r.vehicle] || VEHICLE.car).color }} aria-hidden="true" />{r.vehicle}</span> },
  { key: 'confidence', label: 'Conf.', align: 'right', sortable: true, render: (r) => <span className="font-mono tabular-nums">{r.confidence.toFixed(2)}</span> },
]

export default function Violations() {
  const { snap, step, busy } = useLive()
  const toast = useToast()
  const navigate = useNavigate()
  const { data: d, error, loading, reload } = useGet('/violations', { deps: [snap?.t] })
  const [simError, setSimError] = useState(null)

  async function more() {
    setSimError(null)
    try {
      await step(600)
      logEvent('ui', 'simulated 10 more minutes for the violation log')
      toast({ title: 'Simulated 10 more minutes', body: 'The evidence log has been updated.' })
    } catch (e) {
      setSimError(e?.message ? e : describeError(e))
    }
  }

  const run = <Button icon={Play} loading={busy} onClick={more}>Simulate 10 more minutes</Button>

  return (
    <div>
      <PageHeader eyebrow="05 · violations" title="Violation detection"
        subtitle="Red-light jumping and wrong-way driving are flagged with a plate, a vehicle class and a detector confidence."
        actions={run} />

      {error && <ErrorState error={error} title="Could not load violations" onRetry={reload} />}
      {simError && <div className="mb-4"><ErrorState error={simError} compact title="Simulation failed" onRetry={more} /></div>}
      {loading && !d && (
        <div className="space-y-3" aria-busy="true">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
          <Skeleton className="h-64" />
        </div>
      )}

      {d?.empty && (
        <Card><EmptyState icon={ShieldAlert} title="No violations logged yet"
          body="Simulate a few minutes of traffic. Demand of ×1.0 or more works best, because red-light jumping happens after a long wait."
          action={run} /></Card>
      )}

      {d && !d.empty && (
        <>
          <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4" gap={0.05}>
            <StatCard icon={ShieldAlert} label="Total violations" value={d.kpis.total} sub={`in ${d.minutes} simulated minutes`} tone="warn" />
            <StatCard icon={Siren} label="Red-light jumping" value={d.kpis.red} sub="vehicle crosses stop line on red" tone="alert" />
            <StatCard icon={Ticket} label="Wrong-way driving" value={d.kpis.wrong} sub="enters against traffic flow" tone="alert" />
            <StatCard icon={Gauge} label="Avg confidence" value={`${d.kpis.confidence}`} sub="detector score" tone="info" />
          </Stagger>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card title="Violations by junction">
              <BarsChart data={d.by_junction} xKey="junction" stacked legend height={290} label="Violations by junction"
                bars={[{ key: 'red', label: 'Red-light jumping', color: 'var(--alert)' }, { key: 'wrong', label: 'Wrong-way driving', color: 'var(--warn)' }]} />
            </Card>
            <Card title="Violations per simulated minute">
              <BarsChart data={d.per_minute} xKey="minute" height={290} label="Violations per simulated minute" xName="simulated minute"
                bars={[{ key: 'n', label: 'Violations', color: 'var(--cyan)' }]} labelFormat={(m) => `minute ${m}`} />
            </Card>
          </div>

          <Card title="Evidence log" className="mt-4" action={<span className="font-mono text-[11px] text-dim">newest first</span>}>
            <Table columns={COLUMNS} rows={d.log} rowKey={(r) => `${r.time}-${r.plate}-${r.junction}-${r.approach}`} pageSize={12} dense caption="Violation evidence log"
              cards={(r) => (
                <div className="rounded border border-line bg-panel-2 p-3 text-xs">
                  <div className="mb-1 flex items-center justify-between"><span className="font-mono text-fg">{r.plate}</span><Badge tone={r.kind.startsWith('Red') ? 'alert' : 'warn'}>{r.kind}</Badge></div>
                  <div className="font-mono text-muted">{r.time} · {r.junction} {r.approach} · {r.vehicle} · {r.confidence.toFixed(2)}</div>
                </div>
              )}
              footer={`${d.log.length} most recent of ${d.kpis.total}`} />
          </Card>
        </>
      )}

      <Card title="Violations by controller (last benchmark)" className="mt-4">
        {d?.last_benchmark?.length ? (
          <Table rows={d.last_benchmark} rowKey={(r) => r.controller} dense caption="Violations by controller"
            columns={[
              { key: 'controller', label: 'Controller', render: (r) => <span className="text-fg">{r.controller}</span> },
              { key: 'red', label: 'Red-light', align: 'right', render: (r) => <span className="font-mono tabular-nums">{r.red}</span> },
              { key: 'wrong', label: 'Wrong-way', align: 'right', render: (r) => <span className="font-mono tabular-nums">{r.wrong}</span> },
            ]} />
        ) : (
          <EmptyState icon={Eye} title="No benchmark run yet" body="Run the controller benchmark to compare how many violations each strategy produces."
            action={<Button variant="secondary" onClick={() => navigate('/app/benchmark')}>Open benchmark</Button>} />
        )}
      </Card>

      <p className="mt-4 text-xs text-dim">
        Red-light jumping happens when a red-runner has waited at least 25 s, so controllers that cut waiting time also reduce violations (compare on the Benchmark page).
        Wrong-way drivers are flagged at entry roads.
      </p>
    </div>
  )
}

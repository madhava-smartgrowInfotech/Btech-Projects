import { Boxes, CheckCircle2, Coins, XCircle } from 'lucide-react'
import { useApi } from '../api'
import { Bars } from '../components/charts/Charts'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import Table from '../components/ui/Table'
import { Card, ScoreBar, StatCard } from '../components/ui/display'
import { ErrorState, PageSkeleton } from '../components/ui/feedback'
import { usd } from '../format'
import { useTheme } from '../lib/theme'

const SIGNAL_LABELS = {
  relationships: 'Relationships', funding_rounds: 'Funding rounds', funding_total_usd: 'Total funding',
  milestones: 'Milestones', avg_participants: 'Avg. participants',
}

export default function Insights() {
  const { data: i, error, loading, reload } = useApi('/insights')
  const { tokens } = useTheme()

  if (error) return <><PageHeader title="Startup insights" eyebrow="dataset" /><ErrorState error={error} title="Could not load the insights" onRetry={reload} /></>
  if (loading || !i) return <PageSkeleton />

  const rate = (v) => `${(v * 100).toFixed(0)}%`
  const rateTone = (r) => (r.success_rate >= i.success_rate ? tokens.ok : tokens.warn)
  const funding = [
    { name: 'SUCCESS', value: i.median_funding_success },
    { name: 'FAILURE', value: i.median_funding_failure },
  ]
  const corr = Object.entries(i.correlations).map(([k, v]) => ({ k, label: SIGNAL_LABELS[k] || k, v }))
    .sort((a, b) => Math.abs(b.v) - Math.abs(a.v))

  const cols = (first, key) => [
    { key, label: first, render: (r) => <span className="text-fg">{r[key]}</span>, sortable: true, sortValue: (r) => r[key], defaultDir: 'asc' },
    { key: 'success_rate', label: 'Success rate', align: 'right', sortable: true, render: (r) => <span className="font-mono tabular-nums">{(r.success_rate * 100).toFixed(1)}%</span> },
    { key: 'count', label: 'n', align: 'right', sortable: true, render: (r) => <span className="font-mono tabular-nums text-muted">{r.count}</span> },
  ]

  return (
    <>
      <PageHeader title="Startup insights" eyebrow="dataset"
        subtitle={`Computed live from ${i.total.toLocaleString('en-US')} historical startups in this deployment.`} />

      <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Total" value={i.total} icon={Boxes} />
        <StatCard label="Success" value={i.success} icon={CheckCircle2} tone="ok" />
        <StatCard label="Failure" value={i.failure} icon={XCircle} tone="alert" />
        <StatCard label="Median funding (S / F)" value={`${usd(i.median_funding_success)} / ${usd(i.median_funding_failure)}`} icon={Coins} tone="info" sub="successful / failed startups" />
      </Stagger>

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Success rate by industry" eyebrow="chart">
          <Bars data={i.industries} xKey="industry" layout="horizontal" height={Math.max(260, i.industries.length * 30)} xWidth={96}
            valueFormat={rate} domain={[0, 0.6]} label="Success rate for each industry" legend={false}
            series={[{ key: 'success_rate', label: 'Success rate', color: tokens.ok }]} colorBy={rateTone} refLine={i.success_rate} />
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-dim">dashed line = overall success rate ({(i.success_rate * 100).toFixed(1)}%) · amber = below average</p>
        </Card>
        <Card title="Industry detail" eyebrow="table">
          <Table columns={cols('Industry', 'industry')} rows={i.industries} rowKey={(r) => r.industry} caption="Success rate by industry" dense
            initialSort={{ key: 'count', dir: 'desc' }}
            cards={(r) => (
              <div className="flex items-center justify-between rounded border border-line bg-panel-2 px-3 py-2 text-sm">
                <span>{r.industry}</span><span className="font-mono text-muted">{(r.success_rate * 100).toFixed(1)}% · n={r.count}</span>
              </div>
            )} />
        </Card>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Median funding by outcome" eyebrow="funding distribution">
          <Bars data={funding} xKey="name" height={240} valueFormat={usd} label="Median total funding by outcome" legend={false}
            series={[{ key: 'value', label: 'Median funding', color: tokens.ok }]} colorBy={(r) => (r.name === 'SUCCESS' ? tokens.ok : tokens.alert)} />
        </Card>
        <Card title="Correlation with SUCCESS" eyebrow="signals">
          <div className="space-y-4">
            {corr.map((c) => (
              <div key={c.k}>
                <ScoreBar value={Math.abs(c.v)} label={`${c.label} (r = ${c.v.toFixed(3)})`} tone={() => (c.v >= 0 ? 'ok' : 'alert')} />
              </div>
            ))}
          </div>
          <p className="mt-3 font-mono text-[10px] uppercase tracking-wider text-dim">bar length = |r| · green = positive, red = negative</p>
        </Card>
      </div>

      <Card title="Success rate by state" eyebrow="top states" className="mt-5">
        <Table columns={cols('State', 'state')} rows={i.states} rowKey={(r) => r.state} caption="Success rate by state" dense
          initialSort={{ key: 'count', dir: 'desc' }}
          cards={(r) => (
            <div className="flex items-center justify-between rounded border border-line bg-panel-2 px-3 py-2 text-sm">
              <span>{r.state}</span><span className="font-mono text-muted">{(r.success_rate * 100).toFixed(1)}% · n={r.count}</span>
            </div>
          )} />
      </Card>
    </>
  )
}

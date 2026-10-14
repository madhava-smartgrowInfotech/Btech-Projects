import { CheckCircle2, Clock, History, Play, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useApi } from '../api'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Badge, Card, KeyValueList, StatCard, Timeline } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { num, stamp } from '../format'

const STATUS_TONE = { done: 'ok', running: 'warn', failed: 'alert' }
const secs = (r) => (r.finished_at ? Math.round((new Date(r.finished_at) - new Date(r.started_at)) / 1000) : null)

// Last 10 ecosystem generations (GET /api/pipeline/runs) + the ecosystem currently loaded.
export default function Runs() {
  const runs = useApi('/pipeline/runs')
  const status = useApi('/pipeline/status')
  const rows = runs.data || []
  const chrono = [...rows].reverse()
  const done = rows.filter((r) => r.status === 'done')
  const cur = status.data?.current

  const columns = [
    { key: 'id', label: 'Run', sortable: true, render: (r) => <span className="font-mono text-sm text-fg">#{r.id}</span> },
    { key: 'status', label: 'Status', sortable: true, render: (r) => <Badge tone={STATUS_TONE[r.status] || 'neutral'} dot>{r.status}</Badge> },
    { key: 'seed', label: 'Seed', align: 'right', sortable: true, render: (r) => <span className="font-mono text-xs">{r.seed}</span> },
    { key: 'taxpayers', label: 'Taxpayers', align: 'right', sortable: true, render: (r) => <span className="font-mono text-xs">{num(r.taxpayers)}</span> },
    { key: 'flagged', label: 'Flagged', align: 'right', sortable: true, sortValue: (r) => r.flagged ?? -1, render: (r) => <span className="font-mono text-xs text-alert">{r.flagged ?? '-'}</span> },
    { key: 'dur', label: 'Duration', align: 'right', sortable: true, sortValue: (r) => secs(r) ?? -1, render: (r) => <span className="font-mono text-xs">{secs(r) !== null ? `${secs(r)}s` : '-'}</span> },
    { key: 'started_at', label: 'Started', sortable: true, render: (r) => <span className="whitespace-nowrap font-mono text-xs text-muted">{stamp(r.started_at)}</span> },
  ]

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="// pipeline" title="Run history" subtitle="The last ten ecosystem generations, newest first, and the ecosystem the dashboard is showing now." />
      {runs.error && <ErrorState error={runs.error} onRetry={runs.reload} title="Could not load run history" />}
      {runs.loading && !runs.data ? <Skeleton className="h-36" /> : runs.data && rows.length > 0 && (
        <Stagger className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 xl:grid-cols-4">
          <StatCard icon={History} label="Runs recorded" value={rows.length} sub="most recent ten" spark={chrono} sparkKey="taxpayers" sparkLabel="taxpayers per run" tone="cyan" />
          <StatCard icon={CheckCircle2} label="Completed" value={done.length} sub={`${rows.length - done.length} failed or running`} spark={chrono.map((r) => ({ ok: r.status === 'done' ? 1 : 0 }))} sparkKey="ok" sparkLabel="success per run" />
          <StatCard icon={XCircle} label="Flagged (latest done)" value={done[0]?.flagged ?? 0} format={num} tone="alert" spark={chrono.filter((r) => r.flagged !== null && r.flagged !== undefined)} sparkKey="flagged" sparkLabel="flagged taxpayers per run" live />
          <StatCard icon={Clock} label="Last duration" value={done[0] ? secs(done[0]) : 0} format={(v) => `${Math.round(v)}s`} tone="warn" spark={chrono.filter(secs).map((r) => ({ s: secs(r) }))} sparkKey="s" sparkLabel="seconds per run" />
        </Stagger>
      )}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Card title="Runs" className="xl:col-span-2">
          <Table columns={columns} rows={runs.data} rowKey={(r) => r.id} loading={runs.loading} initialSort={{ key: 'id', dir: 'desc' }}
            empty={<EmptyState icon={History} title="No generations yet" body="The dashboard is showing the bundled base ecosystem. Generate a new one from the control room."
              action={<Link to="/app" className="inline-flex h-8 items-center gap-2 rounded-[6px] bg-ok px-3 text-xs font-medium text-on-ok"><Play size={14} /> Open the generator</Link>} />}
            cards={(r) => (
              <div className="rounded-[6px] border border-line bg-panel-2 p-3">
                <div className="flex items-center justify-between"><span className="font-mono text-sm text-fg">#{r.id}</span><Badge tone={STATUS_TONE[r.status]} dot>{r.status}</Badge></div>
                <div className="mt-1 font-mono text-[11px] text-dim">seed {r.seed} · {r.taxpayers} taxpayers · {r.flagged ?? '-'} flagged · {secs(r) ?? '-'}s</div>
                <div className="font-mono text-[11px] text-dim">{stamp(r.started_at)}</div>
              </div>
            )} />
        </Card>
        <div className="space-y-5">
          <Card title="Loaded now">
            {status.error ? <ErrorState error={status.error} onRetry={status.reload} compact /> : !status.data ? <Skeleton className="h-32" /> : cur ? (
              <KeyValueList items={[['Run key', cur.run_key], ['Seed', cur.seed], ['Taxpayers', num(cur.taxpayers)], ['Dataset', cur.dataset], ['Analysed', stamp(cur.generated_at * 1000)]]} />
            ) : <EmptyState title="Pipeline still loading" body="Wait a few seconds after start-up, then refresh." />}
          </Card>
          <Card title="Timeline">
            {rows.length ? (
              <Timeline items={rows.map((r) => ({
                id: r.id, tone: STATUS_TONE[r.status] || 'dim', time: stamp(r.started_at), title: `Run #${r.id} · seed ${r.seed}`,
                body: r.status === 'failed' ? r.message : `${num(r.taxpayers)} taxpayers${r.flagged !== null && r.flagged !== undefined ? ` · ${r.flagged} flagged` : ''}${secs(r) !== null ? ` · ${secs(r)}s` : ''}`,
              }))} />
            ) : <p className="text-xs text-muted">No runs yet.</p>}
          </Card>
        </div>
      </div>
    </div>
  )
}

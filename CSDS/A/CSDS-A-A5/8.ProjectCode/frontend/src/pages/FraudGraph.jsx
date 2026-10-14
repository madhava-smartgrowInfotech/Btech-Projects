import { Network, RotateCcw, Waypoints } from 'lucide-react'
import { lazy, Suspense } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useApi } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge, Card, PatternTag, RiskBadge } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { inr, pct } from '../format'

const GraphView = lazy(() => import('../components/domain/GraphView'))

function PickList({ items, active, onPick, render, empty }) {
  if (!items.length) return empty
  return (
    <ul className="max-h-80 space-y-1.5 overflow-y-auto pr-1">
      {items.map((it) => (
        <li key={it.id}>
          <button type="button" onClick={() => onPick(it.id)} aria-pressed={active === it.id}
            className={`w-full rounded-[6px] border p-2.5 text-left transition-colors ${active === it.id ? 'border-ok/60 bg-ok/[0.07]' : 'border-line hover:border-line-strong hover:bg-panel-2'}`}>
            {render(it)}
          </button>
        </li>
      ))}
    </ul>
  )
}

export default function FraudGraph() {
  const [params, setParams] = useSearchParams()
  const ring = params.get('ring') || ''
  const cluster = params.get('cluster') || ''
  const q = ring ? `ring=${ring}` : cluster ? `cluster=${cluster}` : ''
  const graph = useApi(`/graph?${q}`)
  const structures = useApi('/structures')
  const chains = useApi('/chains')
  const pick = (k, v) => setParams(v ? { [k]: v } : {})

  const chainCols = [
    { key: 'rank', label: '#', sortable: true, defaultDir: 'asc', render: (c) => <span className="font-mono text-xs text-dim">{c.rank}</span> },
    { key: 'id', label: 'Chain', render: (c) => <div className="space-y-1"><Link to={`/app/chains/${c.id}`} className="font-mono text-sm text-fg hover:text-ok">{c.id}</Link><div><PatternTag p={c.type === 'circular_trading' ? 'circular_trading' : 'shell_entity'} /></div></div> },
    { key: 'path', label: 'Route', render: (c) => <span className="block max-w-md text-xs text-muted">{c.path.map((p) => p.legal_name).join(' → ')}</span> },
    { key: 'n_invoices', label: 'Invoices', align: 'right', sortable: true, render: (c) => <span className="font-mono text-xs">{c.n_invoices}</span> },
    { key: 'value', label: 'Value', align: 'right', sortable: true, render: (c) => <span className="whitespace-nowrap font-mono text-xs">{inr(c.value)}</span> },
    { key: 'itc', label: 'ITC', align: 'right', sortable: true, render: (c) => <span className="whitespace-nowrap font-mono text-xs">{inr(c.itc)}</span> },
    { key: 'score', label: 'Score', align: 'right', sortable: true, render: (c) => <RiskBadge risk={c.score} /> },
  ]

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="// network analytics" title="Fraud rings"
        subtitle="Circular-trading loops and shared-identity clusters found in the buyer-seller network."
        actions={q && <Button variant="secondary" size="sm" icon={RotateCcw} onClick={() => pick()}>Show whole fraud network</Button>} />
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">
        <Card className="xl:col-span-3" title={ring ? `Loop ${ring}` : cluster ? `Cluster ${cluster} and its buyers` : 'Fraud network · every loop, suspicious cluster and flagged taxpayer'}>
          {graph.error ? <ErrorState error={graph.error} onRetry={graph.reload} title="Could not load the graph" />
            : !graph.data ? <Skeleton className="h-[560px]" />
              : <Suspense fallback={<Skeleton className="h-[560px]" />}><GraphView data={graph.data} height={560} /></Suspense>}
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-dim">drag to pan · scroll to zoom · click a node to open the taxpayer · arrows point seller → buyer</p>
        </Card>
        <div className="space-y-5">
          <Card title={`Trade loops${structures.data ? ` (${structures.data.rings.length})` : ''}`}>
            {structures.error ? <ErrorState error={structures.error} onRetry={structures.reload} compact />
              : !structures.data ? <Skeleton className="h-48" />
                : <PickList items={structures.data.rings} active={ring} onPick={(id) => pick('ring', id)}
                  empty={<EmptyState icon={Waypoints} title="No loops found" body="No circular-trading loops in this ecosystem." />}
                  render={(r) => (
                    <>
                      <div className="flex items-center justify-between"><span className="font-mono text-sm text-fg">{r.id}</span><RiskBadge risk={r.score} /></div>
                      <div className="mt-0.5 font-mono text-[10.5px] text-dim">{r.members.length} parties · {inr(r.value)} · {r.months} common months · balance {r.balance.toFixed(2)}</div>
                    </>
                  )} />}
          </Card>
          <Card title={`Identity clusters${structures.data ? ` (${structures.data.clusters.length})` : ''}`}>
            {!structures.data ? (structures.error ? null : <Skeleton className="h-48" />)
              : <PickList items={structures.data.clusters} active={cluster} onPick={(id) => pick('cluster', id)}
                empty={<EmptyState icon={Network} title="No clusters" body="No registrations share an address or contact." />}
                render={(c) => (
                  <>
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2 font-mono text-sm text-fg">{c.id}{c.suspicious ? <Badge tone="alert">suspicious</Badge> : <Badge>group firms</Badge>}</span>
                      <RiskBadge risk={c.score} />
                    </div>
                    <div className="mt-0.5 font-mono text-[10.5px] text-dim">{c.members.length} registrations · {pct(c.young_share)} young · {pct(c.vanished_share)} stopped filing</div>
                  </>
                )} />}
          </Card>
        </div>
      </div>
      <Card title="Invoice chains ranked by risk">
        {chains.error ? <ErrorState error={chains.error} onRetry={chains.reload} title="Could not load chains" /> : (
          <Table columns={chainCols} rows={chains.data} rowKey={(c) => c.id} loading={chains.loading} initialSort={{ key: 'rank', dir: 'asc' }} pageSize={10}
            empty={<EmptyState icon={Waypoints} title="No invoice chains" body="This ecosystem has no circular or shell invoice chains." />}
            cards={(c) => (
              <Link to={`/app/chains/${c.id}`} className="block rounded-[6px] border border-line bg-panel-2 p-3">
                <div className="flex items-center justify-between gap-2"><span className="font-mono text-sm text-fg">#{c.rank} {c.id}</span><RiskBadge risk={c.score} /></div>
                <div className="mt-1 text-xs text-muted">{c.path.map((p) => p.legal_name).join(' → ')}</div>
                <div className="mt-1 font-mono text-[11px] text-dim">{c.n_invoices} invoices · {inr(c.value)} · ITC {inr(c.itc)}</div>
              </Link>
            )} />
        )}
      </Card>
    </div>
  )
}

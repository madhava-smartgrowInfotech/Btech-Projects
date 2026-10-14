import { Activity, FileSearch, FileText, IndianRupee, ShieldAlert, Users } from 'lucide-react'
import { lazy, Suspense } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useApi } from '../api'
import { EvidenceTimeline, InvoiceTable, TaxpayerHeader, TaxpayerLink } from '../components/domain/blocks'
import { Stagger } from '../components/motion'
import { Card, KeyValueList, RiskBadge, ScoreBar, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton, Skeleton } from '../components/ui/feedback'
import { Breadcrumbs, TabPanel, Tabs } from '../components/ui/nav'
import Table from '../components/ui/Table'
import { inr, monthLabel, num } from '../format'

const MonthlyChart = lazy(() => import('../components/domain/MonthlyChart'))
const GraphView = lazy(() => import('../components/domain/GraphView'))

function Network({ gstin, data }) {
  const graph = useApi(`/graph?focus=${gstin}`)
  const partnerCols = [
    { key: 'legal_name', label: 'Partner', sortable: true, defaultDir: 'asc', render: (p) => <TaxpayerLink gstin={p.gstin} name={p.legal_name} sub={false} /> },
    { key: 'bought_from', label: 'Bought from', align: 'right', sortable: true, render: (p) => <span className="font-mono text-xs">{p.bought_from ? inr(p.bought_from) : '-'}</span> },
    { key: 'sold_to', label: 'Sold to', align: 'right', sortable: true, render: (p) => <span className="font-mono text-xs">{p.sold_to ? inr(p.sold_to) : '-'}</span> },
    { key: 'risk', label: 'Risk', align: 'right', sortable: true, render: (p) => <RiskBadge risk={p.risk} /> },
  ]
  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <Card title="Trading network around this taxpayer">
        {graph.error ? <ErrorState error={graph.error} onRetry={graph.reload} title="Could not load the network" />
          : !graph.data ? <Skeleton className="h-[420px]" />
            : <Suspense fallback={<Skeleton className="h-[420px]" />}><GraphView data={graph.data} height={420} /></Suspense>}
        {data.rings.map((r) => (
          <p key={r.id} className="mt-3 rounded-[6px] border border-alert/30 bg-alert/5 p-2.5 font-mono text-[11px] text-alert">
            loop {r.id}: {r.loop.map((m) => m.legal_name).concat(r.loop[0].legal_name).join(' → ')} ({inr(r.value)})
          </p>
        ))}
      </Card>
      <Card title="Main trading partners">
        <Table columns={partnerCols} rows={data.partners} rowKey={(p) => p.gstin} dense initialSort={null}
          empty={<EmptyState icon={Users} title="No trading partners" body="This taxpayer has no invoices in the current ecosystem." />} />
        {data.cluster && (
          <div className="mt-4 rounded-[6px] border border-info/30 bg-info/5 p-3 text-xs text-fg">
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-info">Shared-identity cluster {data.cluster.id} · score {data.cluster.score.toFixed(2)}</div>
            {data.cluster.members.map((m, i) => (
              <span key={m.gstin}>{i > 0 && ', '}<Link className="underline decoration-info/40 hover:text-info" to={`/app/taxpayers/${m.gstin}`}>{m.legal_name}</Link></span>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export default function TaxpayerProfile() {
  const { gstin } = useParams()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'signals'
  const { data, error, loading, reload } = useApi(`/taxpayers/${gstin}`)
  const crumbs = [{ label: 'Taxpayers', to: '/app/taxpayers' }, { label: data?.taxpayer.legal_name || gstin }]

  if (error) return <div className="space-y-4"><Breadcrumbs items={crumbs} /><ErrorState error={error} onRetry={reload} title={`Could not load taxpayer ${gstin}`} /></div>
  if (loading && !data) return <PageSkeleton />
  const t = data.taxpayer
  const monthly = data.monthly.filter((m) => m.present)
  const inv = data.invoice_counts
  const tabs = [
    { id: 'signals', label: 'Signals' }, { id: 'evidence', label: 'Evidence', count: data.evidence.length },
    { id: 'network', label: 'Network', count: data.partners.length }, { id: 'invoices', label: 'Invoices', count: data.flagged_invoices.length },
  ]
  return (
    <div className="space-y-5">
      <Breadcrumbs items={crumbs} />
      <TaxpayerHeader t={t}>
        <Link to={`/app/cases/${gstin}`} className="inline-flex h-9 items-center gap-2 rounded-[6px] bg-ok px-3.5 text-sm font-medium text-on-ok shadow-[0_0_0_1px_var(--ok),0_0_22px_-8px_var(--ok)] hover:brightness-110">
          <FileSearch size={16} /> Open case & explanation
        </Link>
      </TaxpayerHeader>

      <Stagger className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={IndianRupee} label="ITC claimed" value={t.itc_claimed} format={inr} spark={monthly} sparkKey="claimed" sparkLabel="claimed in GSTR-3B / month" />
        <StatCard icon={ShieldAlert} label="ITC at risk" value={t.itc_at_risk} format={inr} tone="warn" spark={monthly} sparkKey="avail" sparkLabel="available in GSTR-2B / month" />
        <StatCard icon={Activity} label="Peak JEPA deviation" value={Math.max(0, ...monthly.map((m) => m.deviation || 0))} format={(v) => `${v.toFixed(1)}x`} tone="info" spark={monthly} sparkKey="deviation" sparkLabel="deviation vs typical / month" live={t.flagged} />
        <StatCard icon={FileText} label="Invoices" value={inv.inbound + inv.outbound} format={num} sub={`${num(inv.inbound)} in · ${num(inv.outbound)} out`} tone="cyan" spark={monthly} sparkKey="outward" sparkLabel="outward supplies / month" />
      </Stagger>

      <Tabs id="profile" label="Taxpayer sections" tabs={tabs} value={tab} onChange={(v) => setParams(v === 'signals' ? {} : { tab: v }, { replace: true })} />
      <TabPanel tabsId="profile" value={tab}>
        {tab === 'signals' && (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
            <Card title="Risk layers">
              <div className="space-y-3.5">
                <ScoreBar label="JEPA overall deviation" value={t.jepa} />
                <ScoreBar label="JEPA behaviour-layer deviation" value={t.behaviour} />
                <ScoreBar label="Network (rings, clusters, exposure)" value={t.network} />
                <ScoreBar label="Invoice anomalies" value={t.invoice} />
              </div>
              <div className="mt-5 border-t border-line pt-3">
                <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.14em] text-dim">Traditional rule checks triggered</div>
                {Object.keys(data.rules).length ? (
                  <KeyValueList items={Object.entries(data.rules).map(([k, v]) => [v, k])} />
                ) : <p className="text-xs text-muted">None of the rules R1-R5 fired.</p>}
              </div>
              <div className="mt-3 rounded-[6px] border border-line bg-panel-2 p-2.5 font-mono text-[11px] text-muted">
                injected label (sample data): {t.label.is_fraud ? <b className="text-alert">{t.label.roles.join(', ')}</b> : <b className="text-ok">legitimate</b>}
              </div>
            </Card>
            <Card title="Monthly ITC · available vs claimed" className="xl:col-span-2">
              <Suspense fallback={<Skeleton className="h-[260px]" />}><MonthlyChart monthly={data.monthly} /></Suspense>
              <p className="mt-2 font-mono text-[10px] text-dim">{data.monthly.length} months · {monthly.length} returns filed · first {monthLabel(data.monthly[0].month)}</p>
            </Card>
          </div>
        )}
        {tab === 'evidence' && (
          <Card title={`Evidence (${data.evidence.length})`}
            action={<Link to={`/app/cases/${gstin}`} className="font-mono text-[11px] uppercase tracking-wider text-ok hover:underline">Read the written explanation →</Link>}>
            <EvidenceTimeline evidence={data.evidence} />
          </Card>
        )}
        {tab === 'network' && <Network gstin={gstin} data={data} />}
        {tab === 'invoices' && (
          <InvoiceTable title={`Anomalous invoices · ${data.flagged_invoices.length} of ${num(inv.inbound + inv.outbound)}`} rows={data.flagged_invoices}
            footer={`${data.flagged_invoices.length} anomalous invoices shown (top 40 by score)`} />
        )}
      </TabPanel>
    </div>
  )
}

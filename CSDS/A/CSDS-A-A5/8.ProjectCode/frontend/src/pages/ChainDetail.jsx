import { FileText, IndianRupee, Receipt, Users } from 'lucide-react'
import { lazy, Suspense, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useApi } from '../api'
import { InvoiceTable, TaxpayerLink } from '../components/domain/blocks'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Card, PatternTag, RiskBadge, StatCard } from '../components/ui/display'
import { ErrorState, PageSkeleton, Skeleton } from '../components/ui/feedback'
import { Breadcrumbs } from '../components/ui/nav'
import Table from '../components/ui/Table'
import { inr, num, pct } from '../format'

const GraphView = lazy(() => import('../components/domain/GraphView'))

export default function ChainDetail() {
  const { id } = useParams()
  const { data, error, loading, reload } = useApi(`/chains/${id}`)
  const graph = useApi(`/graph?chain=${id}`)
  // Per-month series from the chain's own invoices (feeds the KPI sparklines)
  const months = useMemo(() => {
    if (!data) return []
    const m = new Map()
    data.invoices.forEach((r) => {
      const k = r.invoice_date.slice(0, 7)
      const v = m.get(k) || { month: k, invoices: 0, value: 0, tax: 0, parties: new Set() }
      v.invoices += 1
      v.value += r.taxable_value
      v.tax += r.tax_amount
      v.parties.add(r.seller_gstin).add(r.buyer_gstin)
      m.set(k, v)
    })
    return [...m.values()].sort((a, b) => a.month.localeCompare(b.month)).map((v) => ({ ...v, parties: v.parties.size }))
  }, [data])

  const crumbs = [{ label: 'Fraud rings', to: '/app/graph' }, { label: `Chain ${id}` }]
  if (error) return <div className="space-y-4"><Breadcrumbs items={crumbs} /><ErrorState error={error} onRetry={reload} title={`Could not load chain ${id}`} /></div>
  if (loading && !data) return <PageSkeleton />
  const circular = data.type === 'circular_trading'
  const partyCols = [
    { key: 'legal_name', label: 'Taxpayer', sortable: true, defaultDir: 'asc', render: (p) => <TaxpayerLink gstin={p.gstin} name={p.legal_name} /> },
    { key: 'patterns', label: 'Patterns', render: (p) => <div className="flex flex-wrap gap-1">{p.patterns.map((x) => <PatternTag key={x} p={x} />)}</div> },
    { key: 'risk', label: 'Risk', align: 'right', sortable: true, render: (p) => <RiskBadge risk={p.risk} /> },
  ]
  return (
    <div className="space-y-5">
      <Breadcrumbs items={crumbs} />
      <PageHeader eyebrow={`// invoice chain · rank #${data.rank}`} title={`Invoice chain ${data.id}`}
        subtitle={`${data.summary}. Route: ${data.path.map((p) => p.legal_name).join(' → ')}`}
        actions={<><PatternTag p={circular ? 'circular_trading' : 'shell_entity'} /><RiskBadge risk={data.score} /></>} />
      <Stagger className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={FileText} label="Invoices" value={data.invoices_total} format={num} tone="cyan" spark={months} sparkKey="invoices" sparkLabel="invoices / month (shown)" />
        <StatCard icon={IndianRupee} label="Taxable value" value={data.value} format={inr} spark={months} sparkKey="value" sparkLabel="value / month (shown)" />
        <StatCard icon={Receipt} label="ITC passed" value={data.itc} format={inr} tone="warn" spark={months} sparkKey="tax" sparkLabel="tax / month (shown)" live />
        <StatCard icon={Users} label="Parties" value={data.n_parties} format={num} tone="info" sub={`injected-fraud share ${pct(data.label_fraud_share)} (sample labels)`} spark={months} sparkKey="parties" sparkLabel="active parties / month" />
      </Stagger>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Card title="Chain graph">
          {graph.error ? <ErrorState error={graph.error} onRetry={graph.reload} title="Could not load the graph" />
            : !graph.data ? <Skeleton className="h-[420px]" />
              : <Suspense fallback={<Skeleton className="h-[420px]" />}><GraphView data={graph.data} height={420} /></Suspense>}
        </Card>
        <Card title={`Parties (${data.parties.length})`}>
          <Table columns={partyCols} rows={data.parties} rowKey={(p) => p.gstin} initialSort={{ key: 'risk', dir: 'desc' }} dense />
        </Card>
      </div>
      <InvoiceTable title={`Invoices in the chain · ${data.invoices.length} of ${num(data.invoices_total)} shown, by date`} rows={data.invoices}
        footer={`${data.invoices.length} invoices loaded (the API returns the first 150 by date)`} />
    </div>
  )
}

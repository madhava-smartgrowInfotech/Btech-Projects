import { ArrowLeft } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { useApi } from '../api'
import GraphView from '../components/GraphView'
import { Card, ErrorBox, Loading, PatternTag, RiskBadge, Stat } from '../components/ui'
import { inr, pct } from '../format'
import { InvoiceTable } from './TaxpayerProfile'

export default function ChainDetail() {
  const { id } = useParams()
  const { data, error, loading, reload } = useApi(`/chains/${id}`)
  const graph = useApi(`/graph?chain=${id}`)
  if (loading && !data) return <Loading />
  if (error) return <ErrorBox error={error} onRetry={reload} />
  const circular = data.type === 'circular_trading'
  return (
    <div className="space-y-5">
      <Link to="/app/graph" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"><ArrowLeft size={15} /> Fraud rings</Link>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Invoice chain {data.id}</h1>
        <PatternTag p={circular ? 'circular_trading' : 'shell_entity'} />
        <RiskBadge risk={data.score} />
      </div>
      <p className="text-sm text-slate-600">{data.summary}. Route: {data.path.map((p) => p.legal_name).join(' → ')}</p>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat label="Invoices" value={data.invoices_total} />
        <Stat label="Taxable value" value={inr(data.value)} />
        <Stat label="ITC passed" value={inr(data.itc)} tone="amber" />
        <Stat label="Parties" value={data.n_parties} sub={`injected-fraud share ${pct(data.label_fraud_share)} (sample labels)`} />
      </div>
      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Chain graph">
          {graph.loading && !graph.data ? <Loading /> : graph.error ? <ErrorBox error={graph.error} onRetry={graph.reload} /> : <GraphView data={graph.data} height={420} />}
        </Card>
        <Card title="Parties">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500"><th className="pb-2">Taxpayer</th><th className="pb-2">Patterns</th><th className="pb-2 text-right">Risk</th></tr></thead>
              <tbody>
                {data.parties.map((p) => (
                  <tr key={p.gstin} className="border-t border-slate-100">
                    <td className="py-1.5"><Link to={`/app/taxpayers/${p.gstin}`} className="hover:text-indigo-600">{p.legal_name}</Link></td>
                    <td className="py-1.5"><div className="flex flex-wrap gap-1">{p.patterns.map((x) => <PatternTag key={x} p={x} />)}</div></td>
                    <td className="py-1.5 text-right"><RiskBadge risk={p.risk} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
      <InvoiceTable title={`Invoices in the chain (${data.invoices.length} of ${data.invoices_total} shown, by date)`} rows={data.invoices} />
    </div>
  )
}

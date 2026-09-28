import { ArrowLeft, FileSearch } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { useApi } from '../api'
import GraphView from '../components/GraphView'
import MonthlyChart from '../components/MonthlyChart'
import { Card, ErrorBox, Loading, PatternTag, RiskBadge, ScoreBar, Severity } from '../components/ui'
import { inr, SECTORS } from '../format'

export function TaxpayerHeader({ t, children }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-900">{t.legal_name}</h1>
            {t.flagged ? <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">Flagged</span>
              : <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">Not flagged</span>}
          </div>
          <div className="mt-1 font-mono text-sm text-slate-500">{t.gstin}</div>
          <div className="mt-2 text-sm text-slate-600">
            {SECTORS[t.sector]} · {t.constitution} · {t.state} · registered {t.registration_date}
          </div>
          <div className="text-xs text-slate-500">{t.address} · contact {t.contact_id}</div>
          <div className="mt-2 flex flex-wrap gap-1">{t.patterns.map((p) => <PatternTag key={p} p={p} />)}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-500">Risk (rank {t.rank})</div>
          <div className="text-3xl"><RiskBadge risk={t.risk} /></div>
          <div className="mt-2 flex flex-wrap justify-end gap-2">{children}</div>
        </div>
      </div>
    </div>
  )
}

export default function TaxpayerProfile() {
  const { gstin } = useParams()
  const { data, error, loading, reload } = useApi(`/taxpayers/${gstin}`)
  const graph = useApi(`/graph?focus=${gstin}`)
  if (loading && !data) return <Loading />
  if (error) return <ErrorBox error={error} onRetry={reload} />
  const t = data.taxpayer
  return (
    <div className="space-y-5">
      <Link to="/app/taxpayers" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"><ArrowLeft size={15} /> Ranking</Link>
      <TaxpayerHeader t={t}>
        <Link to={`/app/cases/${gstin}`} className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-700">
          <FileSearch size={16} /> Open case & explanation
        </Link>
      </TaxpayerHeader>

      <div className="grid lg:grid-cols-3 gap-5">
        <Card title="Risk layers">
          <div className="space-y-3">
            <ScoreBar label="JEPA overall deviation" value={t.jepa} />
            <ScoreBar label="JEPA behaviour-layer deviation" value={t.behaviour} />
            <ScoreBar label="Network (rings, clusters, exposure)" value={t.network} />
            <ScoreBar label="Invoice anomalies" value={t.invoice} />
          </div>
          <div className="mt-4 border-t border-slate-100 pt-3 text-sm">
            <div className="text-xs text-slate-500 mb-1">Traditional rule checks triggered</div>
            {Object.keys(data.rules).length ? (
              <ul className="space-y-1">{Object.entries(data.rules).map(([k, v]) => <li key={k} className="text-xs text-slate-600"><b>{k}</b> {v}</li>)}</ul>
            ) : <p className="text-xs text-slate-500">None</p>}
          </div>
          <div className="mt-3 rounded-lg bg-slate-50 p-2 text-xs text-slate-500">
            Injected label (sample data): {t.label.is_fraud ? <b className="text-red-600">{t.label.roles.join(', ')}</b> : <b className="text-emerald-600">legitimate</b>}
          </div>
        </Card>
        <Card title="Monthly ITC: available vs claimed" className="lg:col-span-2">
          <MonthlyChart monthly={data.monthly} />
        </Card>
      </div>

      <Card title={`Evidence (${data.evidence.length})`} action={<Link to={`/app/cases/${gstin}`} className="text-xs text-indigo-600 hover:underline">Read the written explanation →</Link>}>
        <ul className="divide-y divide-slate-100">
          {data.evidence.map((e) => (
            <li key={e.id} className="py-2 flex gap-3 text-sm">
              <span className="font-mono text-xs text-indigo-700 pt-0.5">{e.id}</span>
              <div className="flex-1"><div className="flex flex-wrap items-center gap-2"><span className="font-medium text-slate-800">{e.title}</span><Severity s={e.severity} /><span className="text-xs text-slate-400">{e.layer}</span></div>
                <p className="text-slate-600 text-xs mt-0.5">{e.detail}</p></div>
            </li>
          ))}
        </ul>
      </Card>

      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Trading network around this taxpayer">
          {graph.loading && !graph.data ? <Loading /> : graph.error ? <ErrorBox error={graph.error} onRetry={graph.reload} /> : <GraphView data={graph.data} height={400} />}
          {data.rings.map((r) => (
            <p key={r.id} className="mt-2 text-xs text-red-700">Loop {r.id}: {r.loop.map((m) => m.legal_name).concat(r.loop[0].legal_name).join(' → ')} ({inr(r.value)})</p>
          ))}
        </Card>
        <Card title="Main trading partners">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500"><th className="pb-2">Partner</th><th className="pb-2 text-right">Bought from</th><th className="pb-2 text-right">Sold to</th><th className="pb-2 text-right">Risk</th></tr></thead>
              <tbody>
                {data.partners.map((p) => (
                  <tr key={p.gstin} className="border-t border-slate-100">
                    <td className="py-1.5"><Link to={`/app/taxpayers/${p.gstin}`} className="hover:text-indigo-600">{p.legal_name}</Link></td>
                    <td className="py-1.5 text-right">{p.bought_from ? inr(p.bought_from) : '-'}</td>
                    <td className="py-1.5 text-right">{p.sold_to ? inr(p.sold_to) : '-'}</td>
                    <td className="py-1.5 text-right"><RiskBadge risk={p.risk} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.cluster && (
            <div className="mt-3 rounded-lg border border-violet-200 bg-violet-50 p-3 text-xs text-violet-800">
              Shared-identity cluster {data.cluster.id} (score {data.cluster.score.toFixed(2)}):{' '}
              {data.cluster.members.map((m, i) => <span key={m.gstin}>{i > 0 && ', '}<Link className="underline" to={`/app/taxpayers/${m.gstin}`}>{m.legal_name}</Link></span>)}
            </div>
          )}
        </Card>
      </div>

      <InvoiceTable title={`Anomalous invoices (${data.flagged_invoices.length} shown of ${data.invoice_counts.inbound + data.invoice_counts.outbound} total)`} rows={data.flagged_invoices} />
    </div>
  )
}

export function InvoiceTable({ title, rows }) {
  return (
    <Card title={title}>
      {rows.length === 0 ? <p className="text-sm text-slate-500">No anomalous invoices.</p> : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead><tr className="text-left text-slate-500 border-b border-slate-200">
              <th className="py-2 pr-2">Invoice</th><th className="py-2 pr-2">Date</th><th className="py-2 pr-2">Seller → Buyer</th>
              <th className="py-2 pr-2 text-right">Value</th><th className="py-2 pr-2 text-right">Tax</th><th className="py-2 pr-2">E-way</th>
              <th className="py-2 pr-2">In GSTR-1</th><th className="py-2 pr-2">Signals</th><th className="py-2 text-right">Score</th>
            </tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-slate-100 align-top">
                  <td className="py-1.5 pr-2 font-mono">{r.invoice_no}</td>
                  <td className="py-1.5 pr-2 whitespace-nowrap">{r.invoice_date}</td>
                  <td className="py-1.5 pr-2"><Link className="hover:text-indigo-600" to={`/app/taxpayers/${r.seller_gstin}`}>{r.seller_name}</Link> → <Link className="hover:text-indigo-600" to={`/app/taxpayers/${r.buyer_gstin}`}>{r.buyer_name}</Link></td>
                  <td className="py-1.5 pr-2 text-right whitespace-nowrap">{inr(r.taxable_value)}</td>
                  <td className="py-1.5 pr-2 text-right whitespace-nowrap">{inr(r.tax_amount)}</td>
                  <td className="py-1.5 pr-2">{r.eway_bill ? 'yes' : 'no'}</td>
                  <td className="py-1.5 pr-2">{r.seller_reported ? 'yes' : <span className="text-red-600">no</span>}</td>
                  <td className="py-1.5 pr-2 text-slate-500">{r.flags.map((f) => f.replace(/_/g, ' ')).join(', ')}</td>
                  <td className="py-1.5 text-right"><RiskBadge risk={r.anomaly} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

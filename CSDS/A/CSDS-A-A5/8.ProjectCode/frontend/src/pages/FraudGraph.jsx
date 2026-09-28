import { useSearchParams, Link } from 'react-router-dom'
import { useApi } from '../api'
import GraphView from '../components/GraphView'
import { Card, ErrorBox, Loading, PageHeader, PatternTag, RiskBadge } from '../components/ui'
import { inr, pct } from '../format'

export default function FraudGraph() {
  const [params, setParams] = useSearchParams()
  const ring = params.get('ring') || ''
  const cluster = params.get('cluster') || ''
  const q = ring ? `ring=${ring}` : cluster ? `cluster=${cluster}` : ''
  const graph = useApi(`/graph?${q}`)
  const structures = useApi('/structures')
  const chains = useApi('/chains')
  const pick = (k, v) => setParams(v ? { [k]: v } : {})
  const item = (activeId, id) => `w-full text-left rounded-lg border p-2.5 text-sm ${activeId === id ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 hover:border-slate-300'}`

  return (
    <div className="space-y-5">
      <PageHeader title="Fraud rings" subtitle="Circular-trading loops and shared-identity clusters found in the buyer-seller network">
        {q && <button onClick={() => pick()} className="text-sm text-indigo-600 hover:underline">Show whole fraud network</button>}
      </PageHeader>
      <div className="grid xl:grid-cols-4 gap-5">
        <div className="xl:col-span-3">
          <Card title={ring ? `Loop ${ring}` : cluster ? `Cluster ${cluster} and its buyers` : 'Fraud network: every loop, suspicious cluster and flagged taxpayer'}>
            {graph.loading && !graph.data ? <Loading /> : graph.error ? <ErrorBox error={graph.error} onRetry={graph.reload} />
              : <GraphView data={graph.data} height={560} />}
            <p className="mt-2 text-xs text-slate-500">Drag to pan, scroll to zoom, click a node to open the taxpayer. Arrows point from seller to buyer.</p>
          </Card>
        </div>
        <div className="space-y-5">
          <Card title="Trade loops">
            <ErrorBox error={structures.error} onRetry={structures.reload} />
            {structures.loading && !structures.data ? <Loading /> : structures.data && (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {structures.data.rings.map((r) => (
                  <button key={r.id} onClick={() => pick('ring', r.id)} className={item(ring, r.id)}>
                    <div className="flex justify-between"><span className="font-medium">{r.id}</span><RiskBadge risk={r.score} /></div>
                    <div className="text-xs text-slate-500">{r.members.length} parties · {inr(r.value)} · {r.months} common months · balance {r.balance.toFixed(2)}</div>
                  </button>
                ))}
              </div>
            )}
          </Card>
          <Card title="Shared-identity clusters">
            {structures.data && (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {structures.data.clusters.map((c) => (
                  <button key={c.id} onClick={() => pick('cluster', c.id)} className={item(cluster, c.id)}>
                    <div className="flex justify-between"><span className="font-medium">{c.id} {c.suspicious ? <span className="text-xs text-red-600">suspicious</span> : <span className="text-xs text-slate-400">likely group firms</span>}</span><RiskBadge risk={c.score} /></div>
                    <div className="text-xs text-slate-500">{c.members.length} registrations · {pct(c.young_share)} young · {pct(c.vanished_share)} stopped filing</div>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
      <Card title="Invoice chains ranked by risk">
        <ErrorBox error={chains.error} onRetry={chains.reload} />
        {chains.loading && !chains.data ? <Loading /> : chains.data && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                <th className="py-2 pr-2">#</th><th className="py-2 pr-2">Chain</th><th className="py-2 pr-2">Route</th><th className="py-2 pr-2 text-right">Invoices</th>
                <th className="py-2 pr-2 text-right">Value</th><th className="py-2 pr-2 text-right">ITC</th><th className="py-2 text-right">Score</th></tr></thead>
              <tbody>
                {chains.data.map((c) => (
                  <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-2 pr-2 text-slate-400">{c.rank}</td>
                    <td className="py-2 pr-2"><Link to={`/app/chains/${c.id}`} className="font-medium hover:text-indigo-600">{c.id}</Link>
                      <div><PatternTag p={c.type === 'circular_trading' ? 'circular_trading' : 'shell_entity'} /></div></td>
                    <td className="py-2 pr-2 text-xs text-slate-600 max-w-md">{c.path.map((p) => p.legal_name).join(' → ')}</td>
                    <td className="py-2 pr-2 text-right">{c.n_invoices}</td>
                    <td className="py-2 pr-2 text-right">{inr(c.value)}</td>
                    <td className="py-2 pr-2 text-right">{inr(c.itc)}</td>
                    <td className="py-2 text-right"><RiskBadge risk={c.score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

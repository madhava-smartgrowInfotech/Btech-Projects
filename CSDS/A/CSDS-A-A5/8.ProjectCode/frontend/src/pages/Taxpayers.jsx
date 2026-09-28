import { ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useApi } from '../api'
import { Card, ErrorBox, Loading, PageHeader, PATTERN_LABELS, PatternTag, RiskBadge } from '../components/ui'
import { inr, SECTORS } from '../format'

const PAGE = 25

export default function Taxpayers() {
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState(params.get('q') || '')
  const pattern = params.get('pattern') || ''
  const sector = params.get('sector') || ''
  const flagged = params.get('flagged') || ''
  const sort = params.get('sort') || 'risk'
  const page = Number(params.get('page') || 0)
  const set = (k, v) => {
    const p = new URLSearchParams(params)
    v ? p.set(k, v) : p.delete(k)
    if (k !== 'page') p.delete('page')
    setParams(p)
  }
  useEffect(() => {
    const t = setTimeout(() => { if ((params.get('q') || '') !== q) set('q', q) }, 350)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q])
  const qs = new URLSearchParams({ q: params.get('q') || '', pattern, sector, sort, limit: PAGE, offset: page * PAGE })
  if (flagged) qs.set('flagged', flagged)
  const { data, error, loading, reload } = useApi(`/taxpayers?${qs}`)
  const select = 'rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm'

  return (
    <div className="space-y-5">
      <PageHeader title="Taxpayers" subtitle="Ranked by combined risk from the JEPA deviation, network and invoice layers" />
      <Card>
        <div className="flex flex-wrap gap-2 mb-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={16} className="absolute left-2.5 top-2.5 text-slate-400" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name or GSTIN"
              className="w-full rounded-lg border border-slate-300 pl-8 pr-3 py-1.5 text-sm" />
          </div>
          <select value={pattern} onChange={(e) => set('pattern', e.target.value)} className={select}>
            <option value="">All patterns</option>
            {Object.entries(PATTERN_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={sector} onChange={(e) => set('sector', e.target.value)} className={select}>
            <option value="">All sectors</option>
            {Object.entries(SECTORS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={flagged} onChange={(e) => set('flagged', e.target.value)} className={select}>
            <option value="">Flagged + clear</option><option value="true">Flagged only</option><option value="false">Not flagged</option>
          </select>
          <select value={sort} onChange={(e) => set('sort', e.target.value)} className={select}>
            <option value="risk">Sort: risk</option><option value="jepa">Sort: JEPA deviation</option>
            <option value="network">Sort: network</option><option value="invoice">Sort: invoice</option>
            <option value="itc">Sort: ITC at risk</option><option value="name">Sort: name</option>
          </select>
        </div>
        <ErrorBox error={error} onRetry={reload} />
        {loading && !data ? <Loading /> : data && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                    <th className="py-2 pr-2">#</th><th className="py-2 pr-2">Taxpayer</th><th className="py-2 pr-2">Sector</th>
                    <th className="py-2 pr-2">Patterns</th><th className="py-2 pr-2 text-right">JEPA</th><th className="py-2 pr-2 text-right">Network</th>
                    <th className="py-2 pr-2 text-right">Invoice</th><th className="py-2 pr-2 text-right">ITC at risk</th><th className="py-2 text-right">Risk</th>
                  </tr>
                </thead>
                <tbody className={loading ? 'opacity-50' : ''}>
                  {data.items.map((t) => (
                    <tr key={t.gstin} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-2 pr-2 text-slate-400">{t.rank}</td>
                      <td className="py-2 pr-2">
                        <Link to={`/app/taxpayers/${t.gstin}`} className="font-medium text-slate-800 hover:text-indigo-600">{t.legal_name}</Link>
                        <div className="text-xs text-slate-400 font-mono">{t.gstin}</div>
                      </td>
                      <td className="py-2 pr-2 text-slate-600">{SECTORS[t.sector]}</td>
                      <td className="py-2 pr-2"><div className="flex flex-wrap gap-1">{t.patterns.map((p) => <PatternTag key={p} p={p} />)}</div></td>
                      <td className="py-2 pr-2 text-right font-mono text-slate-600">{Math.max(t.jepa, t.behaviour).toFixed(2)}</td>
                      <td className="py-2 pr-2 text-right font-mono text-slate-600">{t.network.toFixed(2)}</td>
                      <td className="py-2 pr-2 text-right font-mono text-slate-600">{t.invoice.toFixed(2)}</td>
                      <td className="py-2 pr-2 text-right">{inr(t.itc_at_risk)}</td>
                      <td className="py-2 text-right"><RiskBadge risk={t.risk} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {data.items.length === 0 && <p className="py-8 text-center text-sm text-slate-500">No taxpayers match these filters.</p>}
            </div>
            <div className="flex items-center justify-between mt-3 text-sm text-slate-600">
              <span>{data.total} taxpayers</span>
              <div className="flex items-center gap-2">
                <button disabled={page === 0} onClick={() => set('page', String(page - 1))} className="p-1 rounded border border-slate-300 disabled:opacity-40"><ChevronLeft size={16} /></button>
                <span>Page {page + 1} of {Math.max(1, Math.ceil(data.total / PAGE))}</span>
                <button disabled={(page + 1) * PAGE >= data.total} onClick={() => set('page', String(page + 1))} className="p-1 rounded border border-slate-300 disabled:opacity-40"><ChevronRight size={16} /></button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}

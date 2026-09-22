import { Camera, ChevronRight, RefreshCw, Search } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../api.js'
import { days, Empty, ErrorBox, Loading, PriorityBadge, SampleBadge, SlaFlag, Spinner, StatusBadge, timeAgo } from '../components/ui.jsx'

const TABS = ['Submitted', 'Assigned', 'In Progress', 'Resolved', 'Rejected']
const TAB_LABEL = { Submitted: 'Awaiting review' }

export default function Queue() {
  const [status, setStatus] = useState('Submitted')
  const [filters, setFilters] = useState({ department: '', priority: '', q: '' })
  const [search, setSearch] = useState('')
  const [data, setData] = useState(null)
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async () => {
    setRefreshing(true)
    try {
      setError('')
      setData((await api.get('/officer/queue', { params: { status, ...filters } })).data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setRefreshing(false)
    }
  }, [status, filters])

  useEffect(() => {
    load()
    const t = setInterval(load, 20000) // new complaints appear without a reload
    return () => clearInterval(t)
  }, [load])
  useEffect(() => {
    api.get('/meta').then((r) => setMeta(r.data)).catch(() => {})
  }, [])

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Triage queue</h1>
          <p className="mt-1 text-sm text-slate-600">AI suggestions are ranked by priority. Open a complaint to review the reasons and decide.</p>
        </div>
        <button className="btn-secondary" onClick={load} disabled={refreshing}>
          {refreshing ? <Spinner /> : <RefreshCw className="h-4 w-4" />} Refresh
        </button>
      </div>

      <div className="mt-5 flex flex-wrap gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setStatus(t)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${status === t ? 'border-brand-700 text-brand-800' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          >
            {TAB_LABEL[t] || t}
            <span className="ml-1.5 rounded-full bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">{data?.counts?.[t] ?? '-'}</span>
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <select className="input w-auto" value={filters.department} onChange={(e) => setFilters({ ...filters, department: e.target.value })} aria-label="Department">
          <option value="">All departments</option>
          {meta?.departments.map((d) => (
            <option key={d.name}>{d.name}</option>
          ))}
        </select>
        <select className="input w-auto" value={filters.priority} onChange={(e) => setFilters({ ...filters, priority: e.target.value })} aria-label="Priority">
          <option value="">All priorities</option>
          {['Critical', 'High', 'Medium', 'Low'].map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            setFilters({ ...filters, q: search })
          }}
        >
          <input className="input w-60" placeholder="Search text or tracking ID" value={search} onChange={(e) => setSearch(e.target.value)} />
          <button className="btn-secondary px-3" aria-label="Search">
            <Search className="h-4 w-4" />
          </button>
        </form>
      </div>

      <div className="mt-4">
        <ErrorBox message={error} onRetry={load} />
      </div>

      <div className="mt-4">
        {data === null ? (
          <Loading />
        ) : data.items.length === 0 ? (
          <div className="card">
            <Empty>No complaints here.</Empty>
          </div>
        ) : (
          <div className="card divide-y divide-slate-100">
            {data.items.map((c) => {
              const cur = c.current
              return (
                <Link key={c.id} to={`/complaints/${c.id}`} className="flex gap-4 p-4 hover:bg-slate-50">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <PriorityBadge priority={cur.priority} />
                      <span className="font-mono text-xs font-semibold text-slate-700">{c.tracking_id}</span>
                      {status !== 'Submitted' && <StatusBadge status={c.status} />}
                      <span className="text-xs text-slate-500">
                        {c.ward || 'No location'} · {c.language} · {timeAgo(c.created_at)}
                      </span>
                      {c.has_photo && <Camera className="h-3.5 w-3.5 text-slate-400" aria-label="Has photo" />}
                      <SampleBadge show={c.is_sample} />
                    </div>
                    <p className="mt-1.5 line-clamp-2 text-sm text-slate-700">{c.text}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-600">
                      <span>
                        <b className="text-slate-800">{cur.category}</b> → <b className="text-slate-800">{cur.department}</b>
                        {!cur.decided && c.ai.department_confidence != null && <span className="text-slate-400"> ({Math.round(c.ai.department_confidence * 100)}% sure)</span>}
                      </span>
                      <span>~{days(cur.expected_days)} to resolve · SLA {cur.sla_days} d</span>
                      <SlaFlag risk={cur.sla_breach_risk && !['Resolved', 'Rejected'].includes(c.status)} breached={cur.sla_breached && !['Resolved', 'Rejected'].includes(c.status)} />
                      {c.top_words.length > 0 && (
                        <span className="flex flex-wrap items-center gap-1">
                          <span className="text-slate-400">key words:</span>
                          {c.top_words.map((w) => (
                            <span key={w} className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-700">
                              {w}
                            </span>
                          ))}
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 shrink-0 self-center text-slate-300" />
                </Link>
              )
            })}
          </div>
        )}
        {data && data.total > data.items.length && <p className="mt-2 text-xs text-slate-500">Showing the first {data.items.length} of {data.total}. Use the filters to narrow down.</p>}
      </div>
    </div>
  )
}

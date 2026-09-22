import { Building2, CalendarClock, FilePlus2, MapPin, MessageSquare, Search } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api, { errorMessage } from '../api.js'
import { Empty, ErrorBox, fmtDate, fmtDay, Loading, SampleBadge, Spinner, StatusBadge } from '../components/ui.jsx'

function Timeline({ items }) {
  return (
    <ol className="relative ml-2 border-l border-slate-200">
      {items.map((e, i) => (
        <li key={i} className="mb-5 ml-5">
          <span className={`absolute -left-[7px] mt-1 h-3.5 w-3.5 rounded-full border-2 border-white ${e.kind === 'reply' ? 'bg-brand-600' : 'bg-slate-400'}`} />
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
            {e.kind === 'reply' ? (
              <span className="inline-flex items-center gap-1 font-semibold text-brand-800">
                <MessageSquare className="h-3.5 w-3.5" /> Reply from the grievance cell
              </span>
            ) : (
              <StatusBadge status={e.status} />
            )}
            {fmtDate(e.at)}
          </div>
          {e.message && <p className="mt-1 whitespace-pre-line text-sm text-slate-700">{e.message}</p>}
        </li>
      ))}
    </ol>
  )
}

function Detail({ c }) {
  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-lg font-semibold text-slate-900">{c.tracking_id}</span>
        <StatusBadge status={c.status} />
        <SampleBadge show={c.is_sample} />
      </div>
      <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-700">{c.text}</p>
      {c.photo_url && <img src={c.photo_url} alt="Complaint" className="mt-3 max-h-56 rounded-lg border border-slate-200" />}
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div className="flex items-start gap-2">
          <Building2 className="mt-0.5 h-4 w-4 text-slate-400" />
          <div>
            <dt className="text-xs text-slate-500">Department</dt>
            <dd className="font-medium text-slate-800">{c.department || 'Under review'}</dd>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <CalendarClock className="mt-0.5 h-4 w-4 text-slate-400" />
          <div>
            <dt className="text-xs text-slate-500">{c.status === 'Resolved' ? 'Resolved on' : 'Expected by'}</dt>
            <dd className="font-medium text-slate-800">
              {c.status === 'Resolved' ? fmtDay(c.resolved_at) : c.expected_by ? fmtDay(c.expected_by) : 'After review'}
            </dd>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <MapPin className="mt-0.5 h-4 w-4 text-slate-400" />
          <div>
            <dt className="text-xs text-slate-500">Ward</dt>
            <dd className="font-medium text-slate-800">{c.ward || 'Not pinned'}</dd>
          </div>
        </div>
      </dl>
      <h3 className="mb-3 mt-6 text-sm font-semibold text-slate-900">Progress</h3>
      <Timeline items={c.timeline} />
    </div>
  )
}

export default function Track() {
  const { trackingId } = useParams()
  const nav = useNavigate()
  const [list, setList] = useState(null)
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState(trackingId || '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    try {
      setError('')
      setList((await api.get('/complaints/mine')).data)
    } catch (err) {
      setError(errorMessage(err))
    }
  }, [])

  const open = useCallback(async (tid) => {
    setBusy(true)
    try {
      setError('')
      setSelected((await api.get(`/complaints/track/${encodeURIComponent(tid)}`)).data)
    } catch (err) {
      setSelected(null)
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])
  useEffect(() => {
    if (trackingId) open(trackingId)
  }, [trackingId, open])
  // live status: refresh the open complaint every 20 s
  useEffect(() => {
    if (!selected) return
    const t = setInterval(() => open(selected.tracking_id), 20000)
    return () => clearInterval(t)
  }, [selected, open])

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">My complaints</h1>
          <p className="mt-1 text-sm text-slate-600">Status updates and replies from the grievance cell appear here.</p>
        </div>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            if (search.trim()) nav(`/track/${search.trim().toUpperCase()}`)
          }}
        >
          <input className="input w-52 font-mono" placeholder="CP-2609-00001" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Tracking ID" />
          <button className="btn-secondary">
            <Search className="h-4 w-4" /> Track
          </button>
        </form>
      </div>
      <div className="mt-4">
        <ErrorBox message={error} onRetry={load} />
      </div>
      <div className="mt-4 grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="space-y-2">
          {list === null ? (
            <Loading />
          ) : list.length === 0 ? (
            <div className="card">
              <Empty>
                You have not filed any complaints yet.
                <div className="mt-3">
                  <Link to="/file" className="btn-primary">
                    <FilePlus2 className="h-4 w-4" /> File a complaint
                  </Link>
                </div>
              </Empty>
            </div>
          ) : (
            list.map((c) => (
              <button
                key={c.id}
                onClick={() => nav(`/track/${c.tracking_id}`)}
                className={`card block w-full p-4 text-left hover:border-brand-600 ${selected?.id === c.id ? 'border-brand-600 ring-2 ring-brand-100' : ''}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-sm font-semibold text-slate-900">{c.tracking_id}</span>
                  <StatusBadge status={c.status} />
                </div>
                <p className="mt-1.5 line-clamp-2 text-sm text-slate-600">{c.text}</p>
                <div className="mt-2 text-xs text-slate-400">{fmtDate(c.created_at)}</div>
              </button>
            ))
          )}
        </div>
        <div>{busy && !selected ? <Loading /> : selected ? <Detail c={selected} /> : <div className="card"><Empty>Select a complaint to see its progress.</Empty></div>}</div>
      </div>
      {busy && selected && (
        <div className="fixed bottom-4 right-4 rounded-full bg-white p-2 shadow">
          <Spinner />
        </div>
      )}
    </div>
  )
}

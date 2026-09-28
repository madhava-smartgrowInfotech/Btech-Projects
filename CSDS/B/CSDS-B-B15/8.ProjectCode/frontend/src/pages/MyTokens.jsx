import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, Plus, ShieldCheck } from 'lucide-react'
import api, { errMsg } from '../api'
import { ErrorBox, SeverityBadge, Spinner, StatusPill } from '../components/ui'

export default function MyTokens() {
  const [rows, setRows] = useState(null)
  const [pending, setPending] = useState([])
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setError('')
    Promise.all([api.get('/bookings/mine'), api.get('/referrals')])
      .then(([b, r]) => {
        setRows(b.data)
        setPending(r.data.filter((x) => x.status === 'pending_consent'))
      })
      .catch((e) => setError(errMsg(e)))
  }, [])
  useEffect(load, [load])

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">My tokens</h1>
        <Link to="/book" className="btn-primary">
          <Plus className="h-4 w-4" /> New booking
        </Link>
      </div>
      {pending.length > 0 && (
        <Link to="/referrals" className="card p-4 flex items-center gap-3 border-amber-300 bg-amber-50">
          <ShieldCheck className="h-5 w-5 text-amber-700" />
          <div className="flex-1 text-sm text-amber-900">
            {pending.length} referral{pending.length > 1 ? 's' : ''} waiting for your consent to share your summary.
          </div>
          <ChevronRight className="h-4 w-4" />
        </Link>
      )}
      <ErrorBox error={error} onRetry={load} />
      {!rows && !error && <Spinner />}
      {rows?.length === 0 && <div className="card p-8 text-center text-slate-500">No bookings yet.</div>}
      {rows?.map((b) => (
        <Link key={b.id} to={`/tokens/${b.id}`} className="card p-4 flex items-center gap-4 hover:border-teal-400">
          <div className="text-center w-16">
            <div className="text-[10px] uppercase text-slate-400">Token</div>
            <div className="text-2xl font-bold text-teal-800">{b.token}</div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">{b.hospital}</div>
            <div className="text-xs text-slate-500">
              {b.date} {b.moved && <span className="text-amber-700">(moved from {b.requested_date})</span>}
              {b.referral_id && <span className="text-violet-700"> - referral</span>}
            </div>
            <div className="mt-1 flex gap-2 items-center">
              <SeverityBadge level={b.severity} />
              <StatusPill status={b.status} />
              {b.status === 'waiting' && <span className="text-xs text-slate-500">#{b.position} - ~{b.wait_min} min</span>}
            </div>
          </div>
          <ChevronRight className="h-4 w-4 text-slate-400" />
        </Link>
      ))}
    </div>
  )
}

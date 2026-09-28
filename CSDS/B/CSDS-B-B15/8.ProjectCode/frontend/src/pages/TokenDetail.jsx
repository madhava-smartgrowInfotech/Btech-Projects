import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ArrowLeft, BellRing, CalendarClock, Radio } from 'lucide-react'
import api, { errMsg } from '../api'
import useQueueSocket from '../components/useQueueSocket'
import { Disclaimer, ErrorBox, SeverityBadge, Spinner, StatusPill } from '../components/ui'

export default function TokenDetail() {
  const { id } = useParams()
  const { state } = useLocation()
  const [b, setB] = useState(state?.justBooked || null)
  const [error, setError] = useState('')
  const [flash, setFlash] = useState('')
  const prev = useRef(null)

  const load = useCallback(() => {
    api
      .get(`/bookings/${id}`)
      .then((r) => {
        const p = prev.current
        if (p && p.position && r.data.position !== p.position) {
          setFlash(r.data.position < p.position ? 'You moved up the queue' : 'An urgent case was placed ahead of you')
          setTimeout(() => setFlash(''), 4000)
        }
        if (p && p.status !== 'called' && r.data.status === 'called') setFlash("It's your turn - please go to the consultation room")
        prev.current = r.data
        setB(r.data)
        setError('')
      })
      .catch((e) => setError(errMsg(e)))
  }, [id])

  useEffect(load, [load])
  const live = useQueueSocket(b?.hospital_id, load)

  if (!b) return error ? <ErrorBox error={error} onRetry={load} /> : <Spinner />

  return (
    <div className="max-w-md mx-auto space-y-4">
      <Link to="/tokens" className="text-sm text-slate-500 inline-flex items-center gap-1">
        <ArrowLeft className="h-4 w-4" /> My tokens
      </Link>
      <ErrorBox error={error} onRetry={load} />
      {state?.justBooked?.allocation && (
        <div className={`card p-3 text-sm ${state.justBooked.moved ? 'bg-amber-50 border-amber-300 text-amber-900' : 'bg-teal-50 border-teal-200 text-teal-900'}`}>
          <CalendarClock className="h-4 w-4 inline mr-1" />
          Booked: {state.justBooked.allocation}
        </div>
      )}
      {flash && (
        <div className="card p-3 text-sm bg-sky-50 border-sky-300 text-sky-900 flex items-center gap-2">
          <BellRing className="h-4 w-4" /> {flash}
        </div>
      )}
      <div className="card overflow-hidden">
        <div className={`px-6 py-8 text-center text-white ${b.status === 'called' ? 'bg-emerald-600' : 'bg-teal-700'}`}>
          <div className="text-xs uppercase tracking-widest opacity-80">Your token</div>
          <div className="text-7xl font-bold my-1">{b.token}</div>
          <div className="text-sm opacity-90">{b.hospital}</div>
          <div className="text-xs opacity-75 mt-1">{b.date}</div>
        </div>
        <div className="p-5 space-y-4">
          {b.status === 'waiting' ? (
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Position</div>
                <div className="text-3xl font-bold">{b.position}</div>
                <div className="text-xs text-slate-400">{b.ahead} ahead of you</div>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Estimated wait</div>
                <div className="text-3xl font-bold">
                  {b.wait_min}
                  <span className="text-base font-medium"> min</span>
                </div>
                <div className="text-xs text-slate-400">around {b.eta?.slice(11)}</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-2">
              <StatusPill status={b.status} />
              <p className="text-sm text-slate-600 mt-2">
                {b.status === 'called' && 'You are being called now. Please proceed to the consultation room.'}
                {b.status === 'done' && 'Consultation completed.'}
                {b.status === 'no_show' && 'Marked as not attended. Please book again if you still need a visit.'}
                {b.status === 'referred' && 'You were referred to another hospital - see Referrals.'}
              </p>
            </div>
          )}
          <div className="flex items-center justify-between text-sm">
            <SeverityBadge level={b.severity} />
            <span className={`inline-flex items-center gap-1 text-xs ${live ? 'text-emerald-600' : 'text-slate-400'}`}>
              <Radio className="h-3.5 w-3.5" /> {live ? 'Live updates on' : 'Reconnecting...'}
            </span>
          </div>
          {b.symptoms?.length > 0 && (
            <div className="text-sm text-slate-600">
              <span className="label inline">Symptoms: </span>
              {b.symptoms.join(', ')}
            </div>
          )}
          {b.status === 'waiting' && (
            <p className="text-xs text-slate-500">
              The wait estimate uses today's actual consultation times and the chance that patients ahead do not turn up. Urgent
              cases may be seen first.
            </p>
          )}
          <Disclaimer />
        </div>
      </div>
    </div>
  )
}

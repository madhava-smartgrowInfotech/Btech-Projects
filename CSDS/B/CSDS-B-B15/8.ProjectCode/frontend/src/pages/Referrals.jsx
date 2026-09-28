import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Check, Lock, ShieldCheck, X } from 'lucide-react'
import api, { errMsg } from '../api'
import { useAuth } from '../auth'
import { ErrorBox, SeverityBadge, Spinner, StatusPill } from '../components/ui'

const STEPS = ['pending_consent', 'sent', 'accepted', 'completed']
const FILTERS = ['all', 'incoming', 'outgoing', 'open', 'closed']

export default function Referrals() {
  const { user } = useAuth()
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const [notice, setNotice] = useState('')
  const [filter, setFilter] = useState('all')

  const load = useCallback(() => {
    api
      .get('/referrals')
      .then((r) => {
        setRows(r.data)
        setError('')
      })
      .catch((e) => setError(errMsg(e)))
  }, [])
  useEffect(load, [load])

  const act = async (r, path, body, msg) => {
    setBusy(`${r.id}${path}`)
    setError('')
    try {
      const { data } = await api.post(`/referrals/${r.id}/${path}`, body)
      setNotice(typeof msg === 'function' ? msg(data) : msg)
      load()
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy('')
    }
  }

  const canReceive = (r) => user.role === 'admin' || (user.role === 'staff' && user.hospital_id === r.to_hospital.id)
  const shown = (rows || []).filter((r) => {
    if (filter === 'incoming') return user.role === 'staff' ? r.to_hospital.id === user.hospital_id : true
    if (filter === 'outgoing') return user.role === 'staff' ? r.from_hospital.id === user.hospital_id : true
    if (filter === 'open') return ['pending_consent', 'sent', 'accepted'].includes(r.status)
    if (filter === 'closed') return ['completed', 'declined'].includes(r.status)
    return true
  })

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex flex-wrap items-center gap-3 justify-between">
        <h1 className="text-xl font-bold">Referrals</h1>
        {user.role !== 'patient' && (
          <div className="flex rounded-lg bg-slate-100 p-1 text-sm">
            {FILTERS.map((f) => (
              <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1 rounded-md capitalize ${filter === f ? 'bg-white shadow text-teal-800' : 'text-slate-500'}`}>
                {f}
              </button>
            ))}
          </div>
        )}
      </div>
      {user.role !== 'patient' && (
        <p className="text-sm text-slate-500">
          Create a referral from the <Link to="/console" className="text-teal-700 underline">hospital console</Link> (Refer on a patient). The
          receiving hospital sees the clinical summary only after the patient consents.
        </p>
      )}
      <ErrorBox error={error} onRetry={load} />
      {notice && <div className="card px-4 py-2 text-sm bg-teal-50 border-teal-200 text-teal-900">{notice}</div>}
      {!rows && !error && <Spinner />}
      {rows && shown.length === 0 && <div className="card p-8 text-center text-slate-500">No referrals.</div>}

      {shown.map((r) => (
        <div key={r.id} className="card p-4 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400">#{r.id}</span>
            <span className="font-semibold">{r.patient_name}</span>
            <StatusPill status={r.status} />
            <span className="text-xs text-slate-400 ml-auto">{r.created_at.replace('T', ' ')}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="rounded-lg bg-slate-100 px-2 py-1">{r.from_hospital.name}</span>
            <ArrowRight className="h-4 w-4 text-slate-400" />
            <span className="rounded-lg bg-teal-50 text-teal-800 px-2 py-1">{r.to_hospital.name}</span>
            <span className="text-xs text-slate-500">({r.specialty})</span>
          </div>
          <div className="text-sm">
            <span className="label inline">Reason: </span>
            {r.reason}
          </div>

          <div className="flex items-center gap-1">
            {STEPS.map((s, i) => {
              const reached = r.status !== 'declined' && STEPS.indexOf(r.status) >= i
              return (
                <div key={s} className="flex-1">
                  <div className={`h-1.5 rounded ${reached ? 'bg-teal-600' : 'bg-slate-200'}`} />
                  <div className={`text-[10px] mt-1 capitalize ${reached ? 'text-teal-800' : 'text-slate-400'}`}>{s.replace('_', ' ')}</div>
                </div>
              )
            })}
          </div>

          {r.summary ? (
            <details className="rounded-lg bg-slate-50 p-3 text-sm">
              <summary className="cursor-pointer font-medium flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-teal-700" /> Shared clinical summary {r.consent ? '(consented)' : '(awaiting consent)'}
              </summary>
              <div className="grid sm:grid-cols-2 gap-x-4 gap-y-1 mt-2">
                <div>Age / gender: {r.summary.age ?? '-'} / {r.summary.gender ?? '-'}</div>
                <div>Visit: {r.summary.visit_date} at {r.summary.referring_hospital}</div>
                <div className="sm:col-span-2">Symptoms: {r.summary.symptoms.join(', ') || '-'}</div>
                <div className="flex items-center gap-1">
                  AI severity: <SeverityBadge level={r.summary.ai_severity} />
                </div>
                <div>AI possible condition: {r.summary.ai_possible_condition || '-'}</div>
                <div className="sm:col-span-2">Clinician notes: {r.summary.clinician_notes || '-'}</div>
                <div className="sm:col-span-2 text-xs text-slate-500">{r.summary.disclaimer}</div>
              </div>
            </details>
          ) : (
            <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500 flex items-center gap-2">
              <Lock className="h-4 w-4" /> Summary locked until the patient consents.
            </div>
          )}

          {r.new_booking && (
            <div className="text-sm rounded-lg border border-teal-200 bg-teal-50 p-2">
              Appointment at {r.to_hospital.name}: token <b>{r.new_booking.token}</b> on {r.new_booking.date}
              {r.new_booking.status === 'waiting' && ` - position ${r.new_booking.position}, ~${r.new_booking.wait_min} min`}
              {user.role === 'patient' && (
                <Link to={`/tokens/${r.new_booking.id}`} className="ml-2 text-teal-700 underline">
                  Live token
                </Link>
              )}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {user.role === 'patient' && r.status === 'pending_consent' && (
              <>
                <button className="btn-primary" disabled={!!busy} onClick={() => act(r, 'consent', { consent: true }, 'Consent given - your summary was shared')}>
                  <Check className="h-4 w-4" /> I consent to share my summary
                </button>
                <button className="btn-outline" disabled={!!busy} onClick={() => act(r, 'consent', { consent: false }, 'Referral declined')}>
                  <X className="h-4 w-4" /> Decline
                </button>
              </>
            )}
            {canReceive(r) && r.status === 'sent' && (
              <>
                <button className="btn-primary" disabled={!!busy} onClick={() => act(r, 'accept', undefined, (d) => `Accepted - ${d.allocation}`)}>
                  <Check className="h-4 w-4" /> Accept and book
                </button>
                <button className="btn-outline" disabled={!!busy} onClick={() => act(r, 'decline', undefined, 'Referral declined')}>
                  Decline
                </button>
              </>
            )}
            {canReceive(r) && r.status === 'accepted' && (
              <button className="btn-primary" disabled={!!busy} onClick={() => act(r, 'complete', undefined, 'Referral marked completed')}>
                <Check className="h-4 w-4" /> Mark completed
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

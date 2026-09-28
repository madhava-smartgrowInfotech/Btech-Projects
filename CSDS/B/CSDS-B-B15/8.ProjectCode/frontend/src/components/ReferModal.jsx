import { useEffect, useState } from 'react'
import { Send, X } from 'lucide-react'
import api, { errMsg } from '../api'
import { ErrorBox, SeverityBadge, Spinner } from './ui'

export default function ReferModal({ booking, onClose, onDone }) {
  const [specialties, setSpecialties] = useState([])
  const [specialty, setSpecialty] = useState(booking.specialty && booking.specialty !== 'Emergency' ? booking.specialty : 'General Medicine')
  const [targets, setTargets] = useState(null)
  const [to, setTo] = useState(null)
  const [reason, setReason] = useState('')
  const [notes, setNotes] = useState('')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/specialties').then((r) => setSpecialties(r.data)).catch(() => {})
  }, [])
  useEffect(() => {
    setTargets(null)
    api
      .get('/referrals/targets', { params: { booking_id: booking.id, specialty } })
      .then((r) => {
        setTargets(r.data.hospitals)
        setTo(r.data.hospitals[0]?.id ?? null)
      })
      .catch((e) => setError(errMsg(e)))
  }, [booking.id, specialty])

  const submit = async () => {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/referrals', {
        booking_id: booking.id,
        to_hospital_id: to,
        specialty,
        reason,
        notes,
        consent_confirmed: consent,
      })
      onDone(data)
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[2000] bg-black/40 grid place-items-center p-4" onClick={onClose}>
      <div className="card w-full max-w-lg max-h-[90vh] overflow-auto p-5 space-y-3" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Refer {booking.patient_name}</h3>
          <button onClick={onClose} aria-label="close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="text-sm text-slate-600 flex items-center gap-2 flex-wrap">
          Token {booking.token} <SeverityBadge level={booking.severity} /> {booking.condition && <span>AI suggestion: {booking.condition}</span>}
        </div>
        <div>
          <label className="label">Department needed</label>
          <select className="input" value={specialty} onChange={(e) => setSpecialty(e.target.value)}>
            {specialties.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Receiving hospital</label>
          {!targets && !error && <Spinner label="Finding hospitals" />}
          <div className="space-y-1 max-h-48 overflow-auto">
            {targets?.map((t) => (
              <label key={t.id} className={`flex gap-2 items-start rounded-lg border p-2 text-sm cursor-pointer ${to === t.id ? 'border-teal-600 bg-teal-50' : 'border-slate-200'}`}>
                <input type="radio" checked={to === t.id} onChange={() => setTo(t.id)} className="mt-1" />
                <div>
                  <div className="font-medium">{t.name}</div>
                  <div className="text-xs text-slate-500">{t.why.join(' - ')}</div>
                </div>
              </label>
            ))}
            {targets?.length === 0 && <div className="text-sm text-slate-500">No hospital with this department found.</div>}
          </div>
        </div>
        <div>
          <label className="label">Reason for referral</label>
          <input className="input" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. needs pulmonology review and chest imaging" />
        </div>
        <div>
          <label className="label">Clinical notes for the receiving doctor</label>
          <textarea className="input" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Findings, vitals, treatment given" />
        </div>
        {booking.has_account ? (
          <p className="text-xs text-slate-500">The patient will be asked in the app to consent before the summary is shared with the receiving hospital.</p>
        ) : (
          <label className="flex gap-2 text-sm">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            The patient consented in person to sharing this summary with the receiving hospital.
          </label>
        )}
        <ErrorBox error={error} />
        <button className="btn-primary w-full" disabled={busy || !to || reason.trim().length < 3 || (!booking.has_account && !consent)} onClick={submit}>
          <Send className="h-4 w-4" /> {busy ? 'Sending...' : 'Send referral'}
        </button>
      </div>
    </div>
  )
}

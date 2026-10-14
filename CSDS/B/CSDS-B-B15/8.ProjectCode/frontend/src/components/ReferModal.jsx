import { useEffect, useState } from 'react'
import { Send } from 'lucide-react'
import api, { describeError } from '../api'
import { Button, Checkbox, Input, Select, Textarea } from './ui/controls'
import { Badge } from './ui/display'
import { ErrorState, Modal, Skeleton } from './ui/feedback'
import { SEVERITY_TONE } from '../format'
import useApi from '../lib/useApi'

/** Refer a patient from the console: department, receiving hospital, reason and notes. */
export default function ReferModal({ booking, onClose, onDone }) {
  const specialties = useApi(() => api.get('/specialties').then((r) => r.data), [])
  const [specialty, setSpecialty] = useState(booking.specialty && booking.specialty !== 'Emergency' ? booking.specialty : 'General Medicine')
  const targets = useApi(
    () => api.get('/referrals/targets', { params: { booking_id: booking.id, specialty } }).then((r) => r.data),
    [booking.id, specialty],
  )
  const [to, setTo] = useState(null)
  const [reason, setReason] = useState('')
  const [notes, setNotes] = useState('')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  // pre-select the best-ranked hospital whenever the list changes
  useEffect(() => {
    setTo(targets.data?.hospitals?.[0]?.id ?? null)
  }, [targets.data])

  const submit = async () => {
    setBusy(true)
    setError(null)
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
      setError(describeError(e))
    } finally {
      setBusy(false)
    }
  }

  const canSend = !busy && to && reason.trim().length >= 3 && (booking.has_account || consent)

  return (
    <Modal
      open
      onClose={onClose}
      title={`Refer ${booking.patient_name}`}
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button icon={Send} loading={busy} disabled={!canSend} onClick={submit}>
            Send referral
          </Button>
        </>
      }
    >
      <div className="max-h-[70vh] space-y-5 overflow-y-auto p-4">
        <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-muted">
          Token {booking.token} <Badge tone={SEVERITY_TONE[booking.severity]}>{booking.severity}</Badge>
          {booking.condition && <span>AI suggestion: {booking.condition}</span>}
        </div>

        <Select
          label="Department needed"
          value={specialty}
          onChange={(e) => setSpecialty(e.target.value)}
          options={(specialties.data || [specialty]).map((s) => [s, s])}
        />

        <div>
          <div id="refer-hospitals" className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-muted">
            Receiving hospital
          </div>
          {targets.loading && !targets.data && <Skeleton className="h-16 w-full" />}
          {targets.error && <ErrorState error={targets.error} onRetry={targets.reload} compact />}
          {targets.data?.hospitals?.length === 0 && (
            <p className="text-sm text-muted">No hospital in the network has this department. Choose another department.</p>
          )}
          <div role="radiogroup" aria-labelledby="refer-hospitals" className="grid gap-2">
            {targets.data?.hospitals?.map((t) => {
              const on = to === t.id
              return (
                <button
                  key={t.id}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  onClick={() => setTo(t.id)}
                  className="rounded-[6px] border border-line-strong bg-panel-2 p-3 text-left text-sm transition-colors hover:border-ok/50"
                  style={on ? { borderColor: 'var(--ok)', background: 'color-mix(in oklab, var(--ok) 8%, var(--panel-2))' } : undefined}
                >
                  <div className="font-medium text-fg">{t.name}</div>
                  <div className="mt-0.5 font-mono text-[11px] text-muted">{t.why.join(' - ')}</div>
                </button>
              )
            })}
          </div>
        </div>

        <Input label="Reason for referral" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. needs pulmonology review and chest imaging" minLength={3} maxLength={500} />
        <Textarea label="Clinical notes for the receiving doctor" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Findings, vitals, treatment given" />

        {booking.has_account ? (
          <p className="text-xs text-muted">The patient will be asked in the app to consent before the summary is shared with the receiving hospital.</p>
        ) : (
          <Checkbox checked={consent} onChange={setConsent} label="The patient consented in person to sharing this summary with the receiving hospital." />
        )}
        {error && <ErrorState error={error} />}
      </div>
    </Modal>
  )
}

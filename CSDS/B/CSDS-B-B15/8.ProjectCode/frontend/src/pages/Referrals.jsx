import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Check, Lock, ShieldCheck, X } from 'lucide-react'
import api, { describeError } from '../api'
import { useAuth } from '../auth'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge, Card, KeyValueList } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import { Stepper, Tabs } from '../components/ui/nav'
import { SEVERITY_TONE, STATUS_TONE, statusLabel } from '../format'
import useApi from '../lib/useApi'

const STEPS = [
  { id: 'pending_consent', label: 'Consent' },
  { id: 'sent', label: 'Sent' },
  { id: 'accepted', label: 'Accepted' },
  { id: 'completed', label: 'Completed' },
]
const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'incoming', label: 'Incoming' },
  { id: 'outgoing', label: 'Outgoing' },
  { id: 'open', label: 'Open' },
  { id: 'closed', label: 'Closed' },
]

export default function Referrals() {
  const { user } = useAuth()
  const toast = useToast()
  const [filter, setFilter] = useState('all')
  const [busy, setBusy] = useState('')
  const list = useApi(() => api.get('/referrals').then((r) => r.data), [])
  const rows = list.data

  const canReceive = (r) => user.role === 'admin' || (user.role === 'staff' && user.hospital_id === r.to_hospital.id)
  const matches = (r, f) => {
    if (f === 'incoming') return user.role === 'staff' ? r.to_hospital.id === user.hospital_id : true
    if (f === 'outgoing') return user.role === 'staff' ? r.from_hospital.id === user.hospital_id : true
    if (f === 'open') return ['pending_consent', 'sent', 'accepted'].includes(r.status)
    if (f === 'closed') return ['completed', 'declined'].includes(r.status)
    return true
  }
  const shown = useMemo(() => (rows || []).filter((r) => matches(r, filter)), [rows, filter]) // eslint-disable-line react-hooks/exhaustive-deps
  const tabs = FILTERS.filter((f) => user.role !== 'patient' || f.id === 'all').map((f) => ({
    ...f,
    count: (rows || []).filter((r) => matches(r, f.id)).length,
  }))

  const act = async (r, path, body, msg) => {
    setBusy(`${r.id}${path}`)
    try {
      const { data } = await api.post(`/referrals/${r.id}/${path}`, body)
      toast({ tone: 'ok', title: typeof msg === 'function' ? msg(data) : msg })
      list.reload()
    } catch (e) {
      toast({ tone: 'alert', title: 'Action failed', body: describeError(e).message })
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow={user.role === 'patient' ? 'patient' : 'hospital referrals'}
        title="Referrals"
        subtitle={
          user.role === 'patient'
            ? 'Referrals made for you. The receiving hospital sees your summary only after you consent.'
            : 'Create a referral from the hospital console (Refer on a patient). The receiving hospital sees the summary only after the patient consents.'
        }
      />

      {user.role !== 'patient' && (
        <div className="mb-5 overflow-x-auto">
          <Tabs id="ref" tabs={tabs} value={filter} onChange={setFilter} label="Filter referrals" />
        </div>
      )}

      {list.error && <div className="mb-5"><ErrorState error={list.error} onRetry={list.reload} /></div>}
      {!rows && !list.error && (
        <div className="space-y-4">
          <Skeleton className="h-56 w-full" />
        </div>
      )}
      {rows && shown.length === 0 && (
        <EmptyState
          icon={ShieldCheck}
          title="No referrals here"
          body={user.role === 'patient' ? 'Your doctor can refer you to another hospital. You will be asked to consent before anything is shared.' : 'Nothing matches this filter yet.'}
        />
      )}

      <div className="space-y-4">
        {shown.map((r) => (
          <Card
            key={r.id}
            title={`#${r.id} - ${r.patient_name}`}
            eyebrow={r.created_at.replace('T', ' ')}
            action={<Badge tone={STATUS_TONE[r.status]} dot>{statusLabel(r.status)}</Badge>}
          >
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
                <span className="rounded-[4px] border border-line-strong px-2 py-1 text-muted">{r.from_hospital.name}</span>
                <ArrowRight size={14} className="text-dim" aria-hidden="true" />
                <span className="rounded-[4px] border border-ok/40 bg-ok/10 px-2 py-1 text-ok">{r.to_hospital.name}</span>
                <span className="text-dim">({r.specialty})</span>
              </div>
              <p className="text-sm text-fg">
                <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Reason </span>
                {r.reason}
              </p>

              <Stepper steps={STEPS} current={r.status === 'declined' ? 'pending_consent' : r.status} failed={r.status === 'declined'} />

              {r.summary ? (
                <details className="rounded-[6px] border border-line bg-panel-2 p-3 text-sm">
                  <summary className="flex cursor-pointer items-center gap-2 font-medium text-fg">
                    <ShieldCheck size={15} className="text-ok" aria-hidden="true" /> Shared clinical summary {r.consent ? '(consented)' : '(awaiting consent)'}
                  </summary>
                  <div className="mt-3">
                    <KeyValueList
                      cols={2}
                      items={[
                        ['Age / gender', `${r.summary.age ?? '-'} / ${r.summary.gender ?? '-'}`],
                        ['Visit', `${r.summary.visit_date} at ${r.summary.referring_hospital}`],
                        ['Symptoms', r.summary.symptoms.join(', ') || '-'],
                        ['AI severity', <Badge key="s" tone={SEVERITY_TONE[r.summary.ai_severity]}>{r.summary.ai_severity}</Badge>],
                        ['AI possible condition', r.summary.ai_possible_condition || '-'],
                        ['Clinician notes', r.summary.clinician_notes || '-'],
                      ]}
                    />
                    <p className="mt-2 text-xs text-muted">{r.summary.disclaimer}</p>
                  </div>
                </details>
              ) : (
                <p className="flex items-center gap-2 rounded-[6px] border border-line bg-panel-2 p-3 text-sm text-muted">
                  <Lock size={14} aria-hidden="true" /> Summary locked until the patient consents.
                </p>
              )}

              {r.new_booking && (
                <div className="rounded-[6px] border border-ok/35 bg-ok/10 p-3 text-sm text-fg">
                  Appointment at {r.to_hospital.name}: token <b className="font-mono">{r.new_booking.token}</b> on {r.new_booking.date}
                  {r.new_booking.status === 'waiting' && ` - position ${r.new_booking.position}, ~${r.new_booking.wait_min} min`}
                  {user.role === 'patient' && (
                    <Link to={`/tokens/${r.new_booking.id}`} className="ml-2 font-medium text-ok underline">
                      Live token
                    </Link>
                  )}
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                {user.role === 'patient' && r.status === 'pending_consent' && (
                  <>
                    <Button icon={Check} loading={busy === `${r.id}consent`} onClick={() => act(r, 'consent', { consent: true }, 'Consent given - your summary was shared')}>
                      I consent to share my summary
                    </Button>
                    <Button variant="secondary" icon={X} disabled={!!busy} onClick={() => act(r, 'consent', { consent: false }, 'Referral declined')}>
                      Decline
                    </Button>
                  </>
                )}
                {canReceive(r) && r.status === 'sent' && (
                  <>
                    <Button icon={Check} loading={busy === `${r.id}accept`} onClick={() => act(r, 'accept', undefined, (d) => `Accepted - ${d.allocation}`)}>
                      Accept and book
                    </Button>
                    <Button variant="secondary" disabled={!!busy} onClick={() => act(r, 'decline', undefined, 'Referral declined')}>
                      Decline
                    </Button>
                  </>
                )}
                {canReceive(r) && r.status === 'accepted' && (
                  <Button icon={Check} loading={busy === `${r.id}complete`} onClick={() => act(r, 'complete', undefined, 'Referral marked completed')}>
                    Mark completed
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

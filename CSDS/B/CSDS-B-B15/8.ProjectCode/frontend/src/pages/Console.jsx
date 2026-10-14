import { useEffect, useState } from 'react'
import { AlertOctagon, Check, GitBranch, PhoneForwarded, Settings, UserX, Users } from 'lucide-react'
import api, { describeError, todayStr } from '../api'
import { useAuth } from '../auth'
import ReferModal from '../components/ReferModal'
import SeverityMix from '../components/SeverityMix'
import useQueueSocket from '../components/useQueueSocket'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Input, Select } from '../components/ui/controls'
import { Badge, Card, StatCard, StatusDot } from '../components/ui/display'
import { EmptyState, ErrorState, Modal, Skeleton, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { SEVERITY_TONE, STATUS_TONE, statusLabel } from '../format'
import useApi from '../lib/useApi'

const GENDER = [
  ['', 'Gender'],
  ['F', 'Female'],
  ['M', 'Male'],
]

const sourceLabel = (b) => {
  const base = b.is_sample ? 'sample data' : b.kind === 'emergency' ? 'emergency' : b.moved ? `moved from ${b.requested_date}` : 'booked online'
  return b.referral_id && b.kind !== 'emergency' ? `${base} - referral` : base
}

// Done / No-show / Refer buttons, shared by the table row and the mobile card
function RowActions({ b, busy, onStatus, onRefer, compact = false }) {
  return (
    <div className={`flex items-center gap-3 ${compact ? 'flex-wrap' : 'justify-end'}`}>
      <button type="button" className="font-mono text-[11px] uppercase tracking-[0.1em] text-alert hover:underline disabled:opacity-40" disabled={!!busy} onClick={() => onStatus(b, 'no_show')}>
        No-show
      </button>
      <button type="button" className="font-mono text-[11px] uppercase tracking-[0.1em] text-info hover:underline" onClick={() => onRefer(b)}>
        Refer
      </button>
    </div>
  )
}

export default function Console() {
  const { user } = useAuth()
  const toast = useToast()
  const [hid, setHid] = useState(() => user.hospital_id || Number(localStorage.getItem('mq_console_hid')) || null)
  const [date, setDate] = useState(todayStr())
  const [busy, setBusy] = useState('')
  const [refer, setRefer] = useState(null)
  const [emergencyOpen, setEmergencyOpen] = useState(false)
  const [limitsOpen, setLimitsOpen] = useState(false)
  const isToday = date === todayStr()

  const hospitals = useApi(
    () => (user.role === 'admin' ? api.get('/hospitals').then((r) => r.data) : Promise.resolve([])),
    [user.role],
  )
  useEffect(() => {
    if (!hid && hospitals.data?.length) setHid(hospitals.data[0].id)
  }, [hid, hospitals.data])
  useEffect(() => {
    if (hid) localStorage.setItem('mq_console_hid', hid)
  }, [hid])

  const queue = useApi(
    () => (hid ? api.get(`/console/${hid}`, { params: { date } }).then((r) => r.data) : Promise.resolve(null)),
    [hid, date],
  )
  const q = queue.data
  const live = useQueueSocket(hid, queue.reload)

  // every queue action: toast on success or failure, then refresh the queue
  const act = async (label, fn, msg) => {
    setBusy(label)
    try {
      const r = await fn()
      toast({ tone: 'ok', title: typeof msg === 'function' ? msg(r.data) : msg })
      queue.reload()
    } catch (e) {
      toast({ tone: 'alert', title: 'Action failed', body: describeError(e).message })
    } finally {
      setBusy('')
    }
  }
  const callNext = () =>
    act(
      'next',
      () => api.post(`/console/${hid}/call-next`),
      (d) => (d.called ? `Calling token ${d.called.token} - ${d.called.patient_name}` : 'Queue is empty'),
    )
  const setStatus = (b, status) => act(`s${b.id}`, () => api.post(`/console/bookings/${b.id}/status`, { status }), `Token ${b.token} marked ${statusLabel(status)}`)

  if (!hid) {
    return hospitals.error ? <ErrorState error={hospitals.error} onRetry={hospitals.reload} /> : <Skeleton className="h-64 w-full" />
  }

  return (
    <div>
      <PageHeader
        eyebrow={user.role === 'admin' ? 'admin - any hospital' : 'hospital desk'}
        title={q?.hospital.name || 'Hospital console'}
        subtitle="Today's queue, live. Call patients in, record outcomes, add emergencies and refer on."
        actions={
          <>
            {user.role === 'admin' && hospitals.data && (
              <Select
                label="Hospital"
                value={String(hid)}
                onChange={(e) => setHid(Number(e.target.value))}
                options={hospitals.data.map((h) => [String(h.id), h.name])}
                className="min-w-56"
              />
            )}
            <Input label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-40" />
            <StatusDot tone={live ? 'ok' : 'warn'} label={live ? 'live' : 'offline'} blink={live} />
            <Button variant="secondary" icon={Settings} disabled={!q} onClick={() => setLimitsOpen(true)}>
              Limits
            </Button>
            <Button variant="danger" icon={AlertOctagon} disabled={!isToday || !q} onClick={() => setEmergencyOpen(true)}>
              Emergency
            </Button>
          </>
        }
      />

      {queue.error && <div className="mb-5"><ErrorState error={queue.error} onRetry={queue.reload} /></div>}
      {!isToday && <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.1em] text-warn">Viewing {date}. Queue actions are available for today only.</p>}

      {!q ? (
        <div className="grid gap-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
          <Skeleton className="h-96 w-full" />
        </div>
      ) : (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard
              live
              label="OP booked"
              value={q.booked}
              format={(v) => `${Math.round(v)} / ${q.hospital.op_limit}`}
              sub={`expected to attend ${q.expected_attendance}`}
              icon={Users}
            />
            <StatCard label="Waiting" value={q.waiting.length} sub={`consult ~${q.consult_min} min each`} />
            <StatCard
              label="Emergency quota"
              value={q.quota_used}
              format={(v) => `${Math.round(v)} / ${q.hospital.emergency_quota}`}
              tone={q.quota_used >= q.hospital.emergency_quota ? 'alert' : 'ok'}
              sub="reserved slots used"
            />
            <Card title="Severity mix" bodyClass="p-4">
              <SeverityMix counts={q.severity_mix} height="h-2.5" showLegend={false} />
              <div className="mt-2 font-mono text-[11px] text-muted">{Object.values(q.severity_mix).reduce((s, n) => s + n, 0)} today</div>
            </Card>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <div className="space-y-4">
              <Card title="Now serving" eyebrow="consultation room">
                <div className="space-y-3">
                  {q.called.length === 0 && (
                    <EmptyState icon={Users} title="Nobody in the room" body="Call the next patient when you are ready." className="py-6" />
                  )}
                  {q.called.map((b) => (
                    <div key={b.id} className="rounded-[6px] border border-ok/40 bg-ok/[0.07] p-3">
                      <div className="flex items-center gap-3">
                        <div className="font-mono text-3xl font-semibold tabular-nums text-ok">{b.token}</div>
                        <div className="min-w-0 flex-1">
                          <div className="truncate font-medium text-fg">{b.patient_name}</div>
                          <div className="truncate font-mono text-[11px] text-muted">
                            {b.age ?? '-'} {b.gender ?? ''} - {b.condition || 'no AI suggestion'}
                          </div>
                        </div>
                        <Badge tone={SEVERITY_TONE[b.severity]}>{b.severity}</Badge>
                      </div>
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        <Button size="sm" variant="secondary" icon={Check} disabled={!!busy} onClick={() => setStatus(b, 'done')}>
                          Done
                        </Button>
                        <Button size="sm" variant="secondary" icon={UserX} disabled={!!busy} onClick={() => setStatus(b, 'no_show')}>
                          No-show
                        </Button>
                        <Button size="sm" variant="secondary" icon={GitBranch} onClick={() => setRefer(b)}>
                          Refer
                        </Button>
                      </div>
                    </div>
                  ))}
                  <Button size="lg" className="w-full" icon={PhoneForwarded} loading={busy === 'next'} disabled={!isToday || !!busy} onClick={callNext}>
                    Call next
                  </Button>
                </div>
              </Card>

              {q.finished.length > 0 && (
                <Card title={`Finished (${q.finished.length})`} eyebrow="outcomes recorded today">
                  <div className="flex flex-wrap gap-2">
                    {q.finished.map((b) => (
                      <span key={b.id} className="inline-flex items-center gap-2 rounded-[4px] border border-line-strong px-2 py-1 font-mono text-[11px] text-muted">
                        <b className="text-fg">{b.token}</b> {b.patient_name}
                        <Badge tone={STATUS_TONE[b.status]}>{statusLabel(b.status)}</Badge>
                      </span>
                    ))}
                  </div>
                </Card>
              )}
            </div>

            <Card title="Waiting queue" eyebrow="ordered by priority, then token" className="lg:col-span-2" bodyClass="p-4">
              <Table
                caption="Waiting queue"
                rows={q.waiting}
                rowKey={(b) => b.id}
                loading={queue.loading}
                empty={<EmptyState icon={Users} title="No one waiting" body="Patients who book online appear here in priority order." />}
                columns={[
                  { key: 'position', label: '#', render: (b) => <span className="text-dim tabular-nums">{b.position}</span> },
                  { key: 'token', label: 'Token', render: (b) => <span className="font-mono font-semibold">{b.token}</span> },
                  {
                    key: 'patient_name',
                    label: 'Patient',
                    render: (b) => (
                      <div>
                        <div className="font-medium text-fg">{b.patient_name}</div>
                        <div className="font-mono text-[10px] text-dim">{sourceLabel(b)}</div>
                      </div>
                    ),
                  },
                  { key: 'severity', label: 'Severity', render: (b) => <Badge tone={SEVERITY_TONE[b.severity]}>{b.severity}</Badge> },
                  { key: 'condition', label: 'AI suggestion', className: 'hidden md:table-cell', render: (b) => <span className="text-xs text-muted">{b.condition || '-'}</span> },
                  { key: 'wait_min', label: 'Wait', align: 'right', render: (b) => <span className="whitespace-nowrap font-mono text-xs">{b.wait_min} min</span> },
                  { key: 'noshow_prob', label: 'No-show', align: 'right', className: 'hidden sm:table-cell', render: (b) => <span className="font-mono text-xs text-muted">{Math.round(b.noshow_prob * 100)}%</span> },
                  { key: 'actions', label: '', align: 'right', render: (b) => <RowActions b={b} busy={busy} onStatus={setStatus} onRefer={setRefer} /> },
                ]}
                cards={(b) => (
                  <div className="panel p-3">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xl font-semibold">{b.token}</span>
                      <div className="min-w-0 flex-1">
                        <div className="truncate font-medium text-fg">{b.patient_name}</div>
                        <div className="font-mono text-[10px] text-dim">{sourceLabel(b)}</div>
                      </div>
                      <Badge tone={SEVERITY_TONE[b.severity]}>{b.severity}</Badge>
                    </div>
                    <div className="mt-2 flex items-center justify-between font-mono text-[11px] text-muted">
                      <span>{b.wait_min} min wait</span>
                      <RowActions b={b} busy={busy} onStatus={setStatus} onRefer={setRefer} compact />
                    </div>
                  </div>
                )}
              />
            </Card>
          </div>
        </div>
      )}

      <Modal open={emergencyOpen} onClose={() => setEmergencyOpen(false)} title="Emergency arrival" size="md">
        <EmergencyForm
          hid={hid}
          onDone={(d) => {
            setEmergencyOpen(false)
            toast({ tone: 'ok', title: `Emergency token ${d.token} added at the front`, body: d.quota_note })
            queue.reload()
          }}
        />
      </Modal>

      <Modal open={limitsOpen} onClose={() => setLimitsOpen(false)} title="Limits and departments" size="lg">
        {q && (
          <LimitsForm
            h={q.hospital}
            onSaved={() => {
              setLimitsOpen(false)
              toast({ tone: 'ok', title: 'Hospital limits saved' })
              queue.reload()
            }}
          />
        )}
      </Modal>

      {refer && (
        <ReferModal
          booking={refer}
          onClose={() => setRefer(null)}
          onDone={(r) => {
            setRefer(null)
            toast({ tone: 'ok', title: `Referral #${r.id} created`, body: `to ${r.to_hospital.name} - ${statusLabel(r.status)}` })
            queue.reload()
          }}
        />
      )}
    </div>
  )
}

function EmergencyForm({ hid, onDone }) {
  const [f, setF] = useState({ patient_name: '', age: '', gender: '', text: '', notes: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const symptoms = f.text.trim() ? (await api.post('/triage/map-text', { text: f.text })).data.symptoms : []
      const { data } = await api.post(`/console/${hid}/emergency`, {
        patient_name: f.patient_name.trim(),
        age: f.age === '' ? null : Number(f.age),
        gender: f.gender || null,
        symptoms,
        notes: f.notes,
      })
      onDone(data)
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4 p-4">
      <Input label="Patient name" value={f.patient_name} onChange={set('patient_name')} required minLength={1} autoFocus />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Age" type="number" min="0" max="120" value={f.age} onChange={set('age')} />
        <Select label="Gender" options={GENDER} value={f.gender} onChange={set('gender')} />
      </div>
      <Input label="Symptoms (optional)" placeholder="e.g. chest pain, sweating" value={f.text} onChange={set('text')} hint="Read by the same symptom mapper as the booking screen." />
      <Input label="Notes (optional)" value={f.notes} onChange={set('notes')} />
      {error && <ErrorState error={error} />}
      <div className="flex justify-end">
        <Button variant="danger" type="submit" loading={busy} icon={AlertOctagon}>
          Insert at front of queue
        </Button>
      </div>
    </form>
  )
}

function LimitsForm({ h, onSaved }) {
  const [f, setF] = useState({ op_limit: h.op_limit, emergency_quota: h.emergency_quota, avg_consult_min: h.avg_consult_min, op_start: h.op_start })
  const [specs, setSpecs] = useState(h.specialties)
  const all = useApi(() => api.get('/specialties').then((r) => r.data), [])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.patch(`/hospitals/${h.id}`, {
        op_limit: Number(f.op_limit),
        emergency_quota: Number(f.emergency_quota),
        avg_consult_min: Number(f.avg_consult_min),
        op_start: f.op_start,
        specialties: specs,
      })
      onSaved()
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={save} className="space-y-5 p-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Input label="Daily OP limit" type="number" min="1" value={f.op_limit} onChange={set('op_limit')} />
        <Input label="Emergency quota / day" type="number" min="0" value={f.emergency_quota} onChange={set('emergency_quota')} />
        <Input label="Avg consult (min)" type="number" step="0.1" min="0.5" value={f.avg_consult_min} onChange={set('avg_consult_min')} />
        <Input label="OP opens" type="time" value={f.op_start} onChange={set('op_start')} />
      </div>
      <div>
        <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Departments</div>
        {all.error && <ErrorState error={all.error} onRetry={all.reload} compact />}
        <div className="flex flex-wrap gap-2">
          {(all.data || specs).map((s) => {
            const on = specs.includes(s)
            return (
              <button
                key={s}
                type="button"
                aria-pressed={on}
                onClick={() => setSpecs(on ? specs.filter((x) => x !== s) : [...specs, s])}
                className="rounded-[4px] border px-2.5 py-1 font-mono text-[11px] transition-colors"
                style={on ? { borderColor: 'var(--ok)', color: 'var(--ok)', background: 'color-mix(in oklab, var(--ok) 10%, transparent)' } : { borderColor: 'var(--line-strong)', color: 'var(--muted)' }}
              >
                {s}
              </button>
            )
          })}
        </div>
      </div>
      <p className="text-xs text-muted">
        When a day reaches its limit (with up to 15% overbooking where predicted no-shows leave room), new bookings move to the next day with space
        automatically. Critical cases use the emergency quota.
      </p>
      {error && <ErrorState error={error} />}
      <div className="flex justify-end">
        <Button type="submit" loading={busy}>
          Save limits
        </Button>
      </div>
    </form>
  )
}

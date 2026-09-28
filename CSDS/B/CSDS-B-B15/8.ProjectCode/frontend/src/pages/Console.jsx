import { useCallback, useEffect, useState } from 'react'
import { AlertOctagon, Check, GitBranch, PhoneForwarded, Radio, Settings, UserX } from 'lucide-react'
import api, { errMsg, todayStr } from '../api'
import { useAuth } from '../auth'
import ReferModal from '../components/ReferModal'
import useQueueSocket from '../components/useQueueSocket'
import { ErrorBox, SeverityBadge, SeverityBar, Spinner, Stat, StatusPill } from '../components/ui'

export default function Console() {
  const { user } = useAuth()
  const [hospitals, setHospitals] = useState([])
  const [hid, setHid] = useState(user.hospital_id || Number(localStorage.getItem('mq_console_hid')) || null)
  const [date, setDate] = useState(todayStr())
  const [q, setQ] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const [notice, setNotice] = useState('')
  const [refer, setRefer] = useState(null)
  const [showEmergency, setShowEmergency] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const isToday = date === todayStr()

  useEffect(() => {
    if (user.role !== 'admin') return
    api
      .get('/hospitals')
      .then((r) => {
        setHospitals(r.data)
        if (!hid && r.data.length) setHid(r.data[0].id)
      })
      .catch((e) => setError(errMsg(e)))
  }, [user.role]) // eslint-disable-line react-hooks/exhaustive-deps

  const load = useCallback(() => {
    if (!hid) return
    api
      .get(`/console/${hid}`, { params: { date } })
      .then((r) => {
        setQ(r.data)
        setError('')
      })
      .catch((e) => setError(errMsg(e)))
  }, [hid, date])
  useEffect(() => {
    setQ(null)
    load()
    if (hid) localStorage.setItem('mq_console_hid', hid)
  }, [load, hid])
  const live = useQueueSocket(hid, load)

  const act = async (label, fn, msg) => {
    setBusy(label)
    setError('')
    try {
      const r = await fn()
      if (msg) setNotice(typeof msg === 'function' ? msg(r.data) : msg)
      load()
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy('')
    }
  }

  const callNext = () =>
    act('next', () => api.post(`/console/${hid}/call-next`), (d) => (d.called ? `Calling token ${d.called.token} - ${d.called.patient_name}` : 'Queue is empty'))
  const setStatus = (b, status) =>
    act(`s${b.id}`, () => api.post(`/console/bookings/${b.id}/status`, { status }), `Token ${b.token} marked ${status.replace('_', '-')}`)

  if (!hid) return error ? <ErrorBox error={error} /> : <Spinner />

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-60">
          <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Hospital console</div>
          {user.role === 'admin' ? (
            <select className="input mt-1 !text-base font-semibold" value={hid} onChange={(e) => setHid(Number(e.target.value))}>
              {hospitals.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name}
                </option>
              ))}
            </select>
          ) : (
            <h1 className="text-xl font-bold">{q?.hospital.name || '...'}</h1>
          )}
        </div>
        <input type="date" className="input !w-auto" value={date} onChange={(e) => setDate(e.target.value)} />
        <span className={`inline-flex items-center gap-1 text-xs ${live ? 'text-emerald-600' : 'text-slate-400'}`}>
          <Radio className="h-3.5 w-3.5" /> {live ? 'Live' : 'Offline'}
        </span>
        <button className="btn-outline" onClick={() => setShowSettings(!showSettings)}>
          <Settings className="h-4 w-4" /> Limits
        </button>
      </div>

      <ErrorBox error={error} onRetry={load} />
      {notice && (
        <div className="card px-4 py-2 text-sm bg-teal-50 border-teal-200 text-teal-900 flex justify-between">
          {notice}
          <button onClick={() => setNotice('')}>x</button>
        </div>
      )}
      {!q && !error && <Spinner />}

      {q && showSettings && <SettingsPanel q={q} onSaved={(m) => { setNotice(m); setShowSettings(false); load() }} />}

      {q && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="OP booked" value={`${q.booked} / ${q.hospital.op_limit}`} sub={`expected to attend: ${q.expected_attendance}`} />
            <Stat label="Waiting" value={q.waiting.length} sub={`consult ~${q.consult_min} min each`} />
            <Stat
              label="Emergency quota"
              value={`${q.quota_used} / ${q.hospital.emergency_quota}`}
              tone={q.quota_used >= q.hospital.emergency_quota ? 'text-red-600' : 'text-slate-900'}
            />
            <Stat
              label="Severity mix"
              value={<SeverityBar mix={q.severity_mix} />}
              sub={['critical', 'severe', 'moderate', 'mild'].map((l) => `${l[0].toUpperCase()}:${q.severity_mix[l] || 0}`).join('  ')}
            />
          </div>

          <div className="grid lg:grid-cols-3 gap-4">
            <div className="space-y-4">
              <div className="card p-4 space-y-3">
                <div className="text-sm font-semibold">Now serving</div>
                {q.called.length === 0 && <div className="text-sm text-slate-400">Nobody in the consultation room</div>}
                {q.called.map((b) => (
                  <div key={b.id} className="rounded-xl bg-emerald-50 border border-emerald-200 p-3">
                    <div className="flex items-center gap-3">
                      <div className="text-3xl font-bold text-emerald-700">{b.token}</div>
                      <div className="flex-1">
                        <div className="font-medium">{b.patient_name}</div>
                        <div className="text-xs text-slate-500">
                          {b.age ?? '-'} {b.gender ?? ''} - {b.condition || 'no AI suggestion'}
                        </div>
                      </div>
                      <SeverityBadge level={b.severity} />
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3">
                      <button className="btn-outline !px-2 text-xs" disabled={!!busy} onClick={() => setStatus(b, 'done')}>
                        <Check className="h-3.5 w-3.5" /> Done
                      </button>
                      <button className="btn-outline !px-2 text-xs" disabled={!!busy} onClick={() => setStatus(b, 'no_show')}>
                        <UserX className="h-3.5 w-3.5" /> No-show
                      </button>
                      <button className="btn-outline !px-2 text-xs" onClick={() => setRefer(b)}>
                        <GitBranch className="h-3.5 w-3.5" /> Refer
                      </button>
                    </div>
                  </div>
                ))}
                <button className="btn-primary w-full !py-3" disabled={!isToday || busy === 'next'} onClick={callNext}>
                  <PhoneForwarded className="h-4 w-4" /> {busy === 'next' ? 'Calling...' : 'Call next'}
                </button>
                <button className="btn-danger w-full" disabled={!isToday} onClick={() => setShowEmergency(!showEmergency)}>
                  <AlertOctagon className="h-4 w-4" /> Add emergency
                </button>
                {!isToday && <p className="text-xs text-slate-500">Queue actions are available for today only.</p>}
              </div>
              {showEmergency && (
                <EmergencyForm
                  hid={hid}
                  onDone={(d) => {
                    setShowEmergency(false)
                    setNotice(`Emergency token ${d.token} added at the front of the queue (${d.quota_note})`)
                    load()
                  }}
                />
              )}
            </div>

            <div className="lg:col-span-2 card overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 text-sm font-semibold flex justify-between">
                Waiting queue <span className="text-slate-400 font-normal">ordered by priority, then token</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
                    <tr>
                      <th className="px-3 py-2 text-left">#</th>
                      <th className="px-3 py-2 text-left">Token</th>
                      <th className="px-3 py-2 text-left">Patient</th>
                      <th className="px-3 py-2 text-left">Severity</th>
                      <th className="px-3 py-2 text-left hidden md:table-cell">AI suggestion</th>
                      <th className="px-3 py-2 text-right">Wait</th>
                      <th className="px-3 py-2 text-right hidden sm:table-cell">No-show</th>
                      <th className="px-3 py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {q.waiting.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-3 py-8 text-center text-slate-400">
                          No one waiting
                        </td>
                      </tr>
                    )}
                    {q.waiting.map((b) => (
                      <tr key={b.id} className={`border-t border-slate-100 ${b.kind === 'emergency' ? 'bg-red-50' : ''}`}>
                        <td className="px-3 py-2 text-slate-400">{b.position}</td>
                        <td className="px-3 py-2 font-bold">{b.token}</td>
                        <td className="px-3 py-2">
                          <div className="font-medium">{b.patient_name}</div>
                          <div className="text-xs text-slate-400">
                            {b.is_sample ? 'sample data' : b.kind === 'emergency' ? 'emergency' : b.moved ? `moved from ${b.requested_date}` : 'booked online'}
                            {b.referral_id && b.kind !== 'emergency' ? ' - referral' : ''}
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <SeverityBadge level={b.severity} />
                        </td>
                        <td className="px-3 py-2 hidden md:table-cell text-xs text-slate-600">{b.condition}</td>
                        <td className="px-3 py-2 text-right whitespace-nowrap">{b.wait_min} min</td>
                        <td className="px-3 py-2 text-right hidden sm:table-cell text-xs text-slate-500">{Math.round(b.noshow_prob * 100)}%</td>
                        <td className="px-3 py-2 text-right whitespace-nowrap">
                          <button className="text-xs text-rose-600 hover:underline mr-2" disabled={!!busy} onClick={() => setStatus(b, 'no_show')}>
                            No-show
                          </button>
                          <button className="text-xs text-violet-700 hover:underline" onClick={() => setRefer(b)}>
                            Refer
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {q.finished.length > 0 && (
                <details className="border-t border-slate-200">
                  <summary className="px-4 py-2 text-sm cursor-pointer text-slate-600">Finished today ({q.finished.length})</summary>
                  <div className="px-4 pb-3 flex flex-wrap gap-2">
                    {q.finished.map((b) => (
                      <span key={b.id} className="text-xs border rounded-lg px-2 py-1 flex items-center gap-1">
                        <b>{b.token}</b> {b.patient_name} <StatusPill status={b.status} />
                      </span>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        </>
      )}
      {refer && (
        <ReferModal
          booking={refer}
          onClose={() => setRefer(null)}
          onDone={(r) => {
            setRefer(null)
            setNotice(`Referral #${r.id} to ${r.to_hospital.name} created (${r.status.replace('_', ' ')})`)
            load()
          }}
        />
      )}
    </div>
  )
}

function EmergencyForm({ hid, onDone }) {
  const [f, setF] = useState({ patient_name: '', age: '', gender: '', text: '', notes: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const symptoms = f.text.trim() ? (await api.post('/triage/map-text', { text: f.text })).data.symptoms : []
      const { data } = await api.post(`/console/${hid}/emergency`, {
        patient_name: f.patient_name,
        age: f.age === '' ? null : Number(f.age),
        gender: f.gender || null,
        symptoms,
        notes: f.notes,
      })
      onDone(data)
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }
  return (
    <form onSubmit={submit} className="card p-4 space-y-2 border-red-300">
      <div className="text-sm font-semibold text-red-700">Emergency arrival</div>
      <input className="input" placeholder="Patient name" required value={f.patient_name} onChange={(e) => setF({ ...f, patient_name: e.target.value })} />
      <div className="grid grid-cols-2 gap-2">
        <input className="input" type="number" placeholder="Age" min="0" max="120" value={f.age} onChange={(e) => setF({ ...f, age: e.target.value })} />
        <select className="input" value={f.gender} onChange={(e) => setF({ ...f, gender: e.target.value })}>
          <option value="">Gender</option>
          <option value="F">Female</option>
          <option value="M">Male</option>
        </select>
      </div>
      <input className="input" placeholder="Symptoms (optional, e.g. chest pain, sweating)" value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })} />
      <input className="input" placeholder="Notes (optional)" value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} />
      <ErrorBox error={error} />
      <button className="btn-danger w-full" disabled={busy}>
        {busy ? 'Adding...' : 'Insert at front of queue'}
      </button>
    </form>
  )
}

function SettingsPanel({ q, onSaved }) {
  const h = q.hospital
  const [f, setF] = useState({ op_limit: h.op_limit, emergency_quota: h.emergency_quota, avg_consult_min: h.avg_consult_min, op_start: h.op_start })
  const [specs, setSpecs] = useState(h.specialties)
  const [all, setAll] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/specialties').then((r) => setAll(r.data)).catch(() => {})
  }, [])
  const save = async () => {
    setBusy(true)
    setError('')
    try {
      await api.patch(`/hospitals/${h.id}`, {
        op_limit: Number(f.op_limit),
        emergency_quota: Number(f.emergency_quota),
        avg_consult_min: Number(f.avg_consult_min),
        op_start: f.op_start,
        specialties: specs,
      })
      onSaved('Hospital limits saved')
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="card p-4 space-y-3">
      <div className="text-sm font-semibold">Daily limits and departments</div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ['op_limit', 'Daily OP limit', 'number'],
          ['emergency_quota', 'Emergency quota / day', 'number'],
          ['avg_consult_min', 'Avg consult (min)', 'number'],
          ['op_start', 'OP opens', 'time'],
        ].map(([k, label, type]) => (
          <div key={k}>
            <label className="label">{label}</label>
            <input className="input" type={type} step={k === 'avg_consult_min' ? '0.1' : '1'} value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} />
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {all.map((s) => (
          <label key={s} className={`text-xs rounded-full border px-2.5 py-1 cursor-pointer ${specs.includes(s) ? 'bg-teal-50 border-teal-400 text-teal-800' : 'border-slate-200 text-slate-500'}`}>
            <input
              type="checkbox"
              className="hidden"
              checked={specs.includes(s)}
              onChange={() => setSpecs(specs.includes(s) ? specs.filter((x) => x !== s) : [...specs, s])}
            />
            {s}
          </label>
        ))}
      </div>
      <p className="text-xs text-slate-500">
        When a day reaches its limit (allowing up to 15% overbooking where predicted no-shows leave room), new bookings move to the next
        day with space automatically. Critical cases use the emergency quota.
      </p>
      <ErrorBox error={error} />
      <button className="btn-primary" disabled={busy} onClick={save}>
        {busy ? 'Saving...' : 'Save'}
      </button>
    </div>
  )
}

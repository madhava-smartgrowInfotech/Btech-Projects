import { useState } from 'react'
import { Bell, Bot, CheckCircle2, Circle, Clock, FileJson, ListChecks, ShieldCheck, ShieldOff, UserRound } from 'lucide-react'
import api, { CATEGORIES, HOSPITALS } from '../api'
import { AssistantPanel, SourcesBar, Timeline } from '../components/RecordViews'
import { Badge, Button, CATEGORY_COLOR, Card, ErrorBox, HOSPITAL_COLOR, Input, Select, Spinner, fmtDate, useAsync } from '../components/ui'

const TABS = [
  { key: 'timeline', label: 'Timeline', icon: UserRound },
  { key: 'consents', label: 'Consents', icon: ShieldCheck },
  { key: 'assistant', label: 'Assistant', icon: Bot },
  { key: 'reminders', label: 'Reminders', icon: Bell },
]

export default function PatientPage() {
  const [tab, setTab] = useState('timeline')
  const [report, setReport] = useState(null)
  const record = useAsync(async () => (await api.get('/records/me')).data, [])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{record.data?.person.name || 'My health record'}</h1>
          {record.data && <p className="text-sm text-slate-500">Born {record.data.person.birth_date} - {record.data.person.gender} - UniHealth ID <span className="font-mono">{record.data.person.id}</span></p>}
        </div>
        <div className="flex flex-wrap gap-1 bg-white border border-slate-200 rounded-lg p-1">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm ${tab === key ? 'bg-teal-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'timeline' && (
        record.loading ? <Spinner label="Fetching your records from every hospital over FHIR..." /> :
          record.error ? <ErrorBox error={record.error} onRetry={record.reload} /> : (
            <>
              <SourcesBar record={record.data} personId="me" />
              <Timeline items={record.data.timeline} onExplain={(r) => { setReport(r); setTab('assistant') }} />
            </>
          )
      )}
      {tab === 'consents' && <Consents />}
      {tab === 'assistant' && <AssistantPanel report={report} onClearReport={() => setReport(null)} />}
      {tab === 'reminders' && <Reminders />}
    </div>
  )
}

function Consents() {
  const consents = useAsync(async () => (await api.get('/consents')).data, [])
  const requests = useAsync(async () => (await api.get('/access/requests')).data, [])
  const [form, setForm] = useState({ hospital: 'B', categories: [...CATEGORIES], days: 90 })
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [openFhir, setOpenFhir] = useState(null)

  const act = async (key, fn) => {
    setBusy(key); setError(null)
    try { await fn(); consents.reload(); requests.reload() } catch (e) { setError(e) } finally { setBusy(null) }
  }
  const grant = (hospital, categories = form.categories, days = form.days) =>
    act(`grant-${hospital}`, () => api.post('/consents', { hospital, categories, days: Number(days) || null }))
  const toggleCat = (c) => setForm((f) => ({ ...f, categories: f.categories.includes(c) ? f.categories.filter((x) => x !== c) : [...f.categories, c] }))
  const blocked = (requests.data || []).filter((r) => r.status === 'blocked')

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <div className="space-y-4">
        <Card title="Grant access" icon={ShieldCheck}>
          <div className="space-y-3">
            <Select label="Hospital" value={form.hospital} onChange={(e) => setForm({ ...form, hospital: e.target.value })}>
              {Object.entries(HOSPITALS).map(([k, n]) => <option key={k} value={k}>{n}</option>)}
            </Select>
            <div>
              <div className="text-sm font-medium text-slate-700 mb-1">Data categories</div>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((c) => (
                  <label key={c} className="flex items-center gap-1.5 text-sm capitalize">
                    <input type="checkbox" checked={form.categories.includes(c)} onChange={() => toggleCat(c)} className="accent-teal-600" /> {c}
                  </label>
                ))}
              </div>
            </div>
            <Input label="Valid for (days, empty = no expiry)" type="number" min="1" value={form.days} onChange={(e) => setForm({ ...form, days: e.target.value })} />
            <Button loading={busy === `grant-${form.hospital}`} disabled={!form.categories.length} onClick={() => grant(form.hospital)} className="w-full">Grant consent</Button>
          </div>
        </Card>
        <Card title="Access requests" icon={Clock}>
          {requests.loading ? <Spinner /> : requests.error ? <ErrorBox error={requests.error} onRetry={requests.reload} /> : (
            <ul className="space-y-2">
              {(requests.data || []).length === 0 && <li className="text-sm text-slate-500">No doctor has requested your record yet.</li>}
              {requests.data.slice(0, 10).map((r) => (
                <li key={r.id} className="text-sm border border-slate-200 rounded-lg p-2">
                  <div className="flex justify-between gap-2"><span className="font-medium">{r.doctor}</span>
                    <Badge color={r.status === 'blocked' ? 'amber' : 'green'}>{r.status === 'blocked' ? 'awaiting you' : r.status}</Badge></div>
                  <div className="text-xs text-slate-500">{r.reason} - {fmtDate(r.created_at)}</div>
                  {r.status === 'blocked' && blocked.find((b) => b.hospital === r.hospital)?.id === r.id && (
                    <Button className="mt-2" loading={busy === `grant-${r.hospital}`} onClick={() => grant(r.hospital, [...CATEGORIES], 90)}>Approve for {r.hospital_name}</Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
      <Card title="My consents (FHIR Consent resources)" icon={ListChecks} className="lg:col-span-2">
        <ErrorBox error={error} />
        {consents.loading ? <Spinner /> : consents.error ? <ErrorBox error={consents.error} onRetry={consents.reload} /> : (
          <ul className="space-y-2 mt-2">
            {consents.data.length === 0 && <li className="text-sm text-slate-500">No consents yet. Doctors from other hospitals cannot see your record.</li>}
            {consents.data.map((c) => (
              <li key={c.id} className={`border rounded-lg p-3 ${c.status === 'active' ? 'border-teal-200 bg-teal-50/40' : 'border-slate-200 opacity-75'}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge color={HOSPITAL_COLOR[c.hospital]}>{c.hospital_name}</Badge>
                    <Badge color={c.status === 'active' ? 'green' : 'slate'}>{c.status}</Badge>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" onClick={() => setOpenFhir(openFhir === c.id ? null : c.id)}><FileJson className="w-4 h-4" /> FHIR</Button>
                    {c.status === 'active' && (
                      <Button variant="danger" loading={busy === c.id} onClick={() => act(c.id, () => api.post(`/consents/${c.id}/revoke`))}><ShieldOff className="w-4 h-4" /> Revoke</Button>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">{c.categories.map((x) => <Badge key={x} color={CATEGORY_COLOR[x]}>{x}</Badge>)}</div>
                <div className="text-xs text-slate-500 mt-1">Granted {fmtDate(c.created_at)} - {c.expires ? `expires ${fmtDate(c.expires)}` : 'no expiry'}{c.status !== 'active' ? ` - revoked ${fmtDate(c.updated_at)}` : ''}</div>
                {openFhir === c.id && <pre className="mt-2 text-xs bg-slate-900 text-slate-100 rounded-lg p-3 overflow-auto max-h-72">{JSON.stringify(c.fhir, null, 2)}</pre>}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}

function Reminders() {
  const list = useAsync(async () => (await api.get('/reminders')).data, [])
  const [form, setForm] = useState({ text: '', due: new Date().toISOString().slice(0, 10) })
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const act = async (key, fn) => {
    setBusy(key); setError(null)
    try { list.setData((await fn()).data) } catch (e) { setError(e) } finally { setBusy(null) }
  }
  const stateColor = { overdue: 'rose', 'due today': 'amber', upcoming: 'blue', done: 'green' }
  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card title="Reminders" icon={Bell} className="lg:col-span-2">
        <ErrorBox error={error} />
        {list.loading ? <Spinner /> : list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : (
          <ul className="divide-y divide-slate-100">
            {list.data.length === 0 && <li className="text-sm text-slate-500 py-3">No reminders yet. They appear from active prescriptions and follow-up plans.</li>}
            {list.data.map((r) => (
              <li key={r.id} className="py-2 flex items-center gap-3">
                <button disabled={busy === r.id} onClick={() => act(r.id, () => api.post(`/reminders/${r.id}/toggle`))} title="Mark done">
                  {r.done ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <Circle className="w-5 h-5 text-slate-400" />}
                </button>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm ${r.done ? 'line-through text-slate-400' : 'text-slate-800'}`}>{r.text}</div>
                  <div className="text-xs text-slate-500">{r.kind === 'medication' ? 'Daily medication' : r.kind} - {r.source}</div>
                </div>
                <div className="text-right">
                  <Badge color={stateColor[r.state]}>{r.state}</Badge>
                  <div className="text-xs text-slate-500 mt-0.5">{fmtDate(r.due)}</div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title="Add a reminder" icon={Clock}>
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); act('add', () => api.post('/reminders', form)).then(() => setForm({ ...form, text: '' })) }}>
          <Input label="What" value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} placeholder="e.g. Book blood test" required />
          <Input label="Due" type="date" value={form.due} onChange={(e) => setForm({ ...form, due: e.target.value })} required />
          <Button type="submit" loading={busy === 'add'} className="w-full">Add reminder</Button>
        </form>
      </Card>
    </div>
  )
}

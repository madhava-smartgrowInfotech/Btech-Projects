import { useState } from 'react'
import { Building2, ClipboardPlus, Fingerprint, RefreshCcw, Search, Server, UploadCloud } from 'lucide-react'
import api, { HOSPITALS } from '../api'
import { useAuth } from '../App.jsx'
import { Badge, Button, Card, ErrorBox, HOSPITAL_COLOR, Input, Spinner, fmtDate, useAsync } from '../components/ui'

export default function HospitalConsole() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const [hkey, setHkey] = useState(user.hospital || 'A')
  const hospitals = useAsync(async () => (await api.get('/hospitals')).data, [])
  const summaries = useAsync(async () => (await api.get('/sync')).data, [])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2"><Building2 className="w-6 h-6 text-teal-600" />
        {isAdmin ? 'Hospitals & Master Patient Index' : `Hospital console - ${user.hospital_name}`}</h1>

      <Card title="FHIR R4 servers" icon={Server} actions={<Button variant="secondary" onClick={hospitals.reload} loading={hospitals.loading}>Refresh</Button>}>
        {hospitals.error ? <ErrorBox error={hospitals.error} onRetry={hospitals.reload} /> : !hospitals.data ? <Spinner /> : (
          <div className="grid sm:grid-cols-3 gap-3">
            {hospitals.data.map((h) => (
              <button key={h.key} disabled={!isAdmin} onClick={() => setHkey(h.key)}
                className={`text-left rounded-lg border p-3 ${hkey === h.key ? 'border-teal-500 ring-1 ring-teal-500' : 'border-slate-200'} ${isAdmin ? 'hover:bg-slate-50' : 'cursor-default'}`}>
                <div className="flex items-center justify-between gap-2">
                  <Badge color={HOSPITAL_COLOR[h.key]}>{h.name}</Badge>
                  <span className={`text-xs ${h.online ? 'text-emerald-600' : 'text-rose-600'}`}>● {h.online ? `FHIR ${h.fhir_version}` : 'offline'}</span>
                </div>
                <div className="font-mono text-xs text-slate-500 mt-2 break-all">{h.base_url}</div>
                {h.online ? (
                  <div className="flex flex-wrap gap-1 mt-2">{Object.entries(h.counts).map(([t, n]) => <span key={t} className="text-xs text-slate-600 bg-slate-100 rounded px-1.5">{t} {n}</span>)}</div>
                ) : <div className="text-xs text-rose-600 mt-2">{h.error}</div>}
              </button>
            ))}
          </div>
        )}
      </Card>

      <div className="grid lg:grid-cols-3 gap-4">
        <PatientsAndVisit key={hkey} hkey={hkey} onSynced={() => { summaries.reload(); hospitals.reload() }} />
        <Card title="Summaries pushed to UniHealth" icon={UploadCloud}>
          {summaries.loading ? <Spinner /> : summaries.error ? <ErrorBox error={summaries.error} onRetry={summaries.reload} /> : (
            <ul className="space-y-2">
              {summaries.data.length === 0 && <li className="text-sm text-slate-500">No summaries yet.</li>}
              {summaries.data.map((s) => (
                <li key={s.id} className="text-sm border border-slate-200 rounded-lg p-2">
                  <div className="flex justify-between"><Badge color={HOSPITAL_COLOR[s.hospital]}>{s.hospital_name}</Badge><span className="text-xs text-slate-500">{fmtDate(s.received_at)}</span></div>
                  <div className="text-xs text-slate-600 mt-1">Patient <span className="font-mono">{s.local_id}</span> → {s.person_id || 'unlinked'} - {s.entries} FHIR entries</div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
      {isAdmin && <MpiPanel />}
    </div>
  )
}

function PatientsAndVisit({ hkey, onSynced }) {
  const [q, setQ] = useState('')
  const patients = useAsync(async () => (await api.get(`/hospitals/${hkey}/patients`, { params: { q } })).data, [hkey])
  const [sel, setSel] = useState(null)
  const [form, setForm] = useState({ visit_type: 'Outpatient consultation', diagnosis: '', medication: '', dosage: '', follow_up_days: 30 })
  const [state, setState] = useState({ loading: false, error: null, result: null })

  const submit = async (e) => {
    e.preventDefault()
    setState({ loading: true, error: null, result: null })
    try {
      const { data } = await api.post(`/hospitals/${hkey}/visits`, { ...form, patient_id: sel.local_id, follow_up_days: Number(form.follow_up_days) || null })
      setState({ loading: false, error: null, result: data })
      onSynced()
    } catch (err) { setState({ loading: false, error: err, result: null }) }
  }

  return (
    <Card title={`Patients at ${HOSPITALS[hkey]}`} icon={Search} className="lg:col-span-2">
      <form className="flex gap-2 mb-3" onSubmit={(e) => { e.preventDefault(); patients.reload() }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by name" className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <Button type="submit" variant="secondary" loading={patients.loading}>Filter</Button>
      </form>
      {patients.error && <ErrorBox error={patients.error} onRetry={patients.reload} />}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="max-h-96 overflow-auto border border-slate-200 rounded-lg divide-y divide-slate-100">
          {patients.loading && <Spinner />}
          {patients.data?.map((p) => (
            <button key={p.local_id} onClick={() => { setSel(p); setState({ loading: false, error: null, result: null }) }}
              className={`w-full text-left px-3 py-2 text-sm ${sel?.local_id === p.local_id ? 'bg-teal-50' : 'hover:bg-slate-50'}`}>
              <div className="font-medium text-slate-800">{p.name}</div>
              <div className="text-xs text-slate-500"><span className="font-mono">{p.local_id}</span> - {p.birth_date} - {p.gender}</div>
            </button>
          ))}
        </div>
        <div>
          {!sel ? <p className="text-sm text-slate-500">Select a patient to record a treatment episode. The record stays at this hospital; a FHIR summary is pushed to UniHealth.</p> : (
            <form onSubmit={submit} className="space-y-2">
              <div className="text-sm font-medium text-slate-800 flex items-center gap-1"><ClipboardPlus className="w-4 h-4 text-teal-600" /> Visit for {sel.name}</div>
              <Input label="Visit type" value={form.visit_type} onChange={(e) => setForm({ ...form, visit_type: e.target.value })} />
              <Input label="Diagnosis" value={form.diagnosis} onChange={(e) => setForm({ ...form, diagnosis: e.target.value })} required placeholder="e.g. Essential hypertension" />
              <Input label="Medication (optional)" value={form.medication} onChange={(e) => setForm({ ...form, medication: e.target.value })} placeholder="e.g. Amlodipine 5 MG Oral Tablet" />
              <Input label="Dosage" value={form.dosage} onChange={(e) => setForm({ ...form, dosage: e.target.value })} placeholder="e.g. 1 tablet every morning" />
              <Input label="Follow-up in (days)" type="number" min="1" value={form.follow_up_days} onChange={(e) => setForm({ ...form, follow_up_days: e.target.value })} />
              <Button type="submit" loading={state.loading} className="w-full"><RefreshCcw className="w-4 h-4" /> Record visit & sync summary</Button>
              <ErrorBox error={state.error} />
              {state.result && (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-2 text-xs text-emerald-800">
                  Saved {state.result.created.entry.length} FHIR resources at the hospital. Pushed a summary of {state.result.sync.pushed_entries} entries
                  to UniHealth (person {state.result.sync.platform.person_id}); {state.result.sync.platform.reminders_added} reminder(s) created.
                </div>
              )}
            </form>
          )}
        </div>
      </div>
    </Card>
  )
}

function MpiPanel() {
  const persons = useAsync(async () => (await api.get('/mpi/persons')).data, [])
  const [rebuild, setRebuild] = useState({ loading: false, error: null, data: null })
  const [onlyLinked, setOnlyLinked] = useState(true)
  const run = async () => {
    setRebuild({ loading: true, error: null, data: null })
    try { setRebuild({ loading: false, error: null, data: (await api.post('/mpi/rebuild')).data }); persons.reload() } catch (e) { setRebuild({ loading: false, error: e, data: null }) }
  }
  const shown = (persons.data || []).filter((p) => !onlyLinked || p.links.length > 1)
  return (
    <Card title="Master Patient Index" icon={Fingerprint}
      actions={<>
        <label className="flex items-center gap-1 text-sm text-slate-600"><input type="checkbox" checked={onlyLinked} onChange={(e) => setOnlyLinked(e.target.checked)} className="accent-teal-600" /> linked only</label>
        <Button loading={rebuild.loading} onClick={run}><RefreshCcw className="w-4 h-4" /> Re-run linkage</Button>
      </>}>
      <ErrorBox error={rebuild.error} />
      {rebuild.data && <p className="text-sm text-emerald-700 mb-2">Linked {rebuild.data.records} hospital records into {rebuild.data.persons} persons ({rebuild.data.linked_persons} seen at more than one hospital).</p>}
      {persons.loading ? <Spinner /> : persons.error ? <ErrorBox error={persons.error} onRetry={persons.reload} /> : (
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-slate-500 border-b"><th className="py-2 pr-3">Person</th><th className="pr-3">Hospital records (name as recorded, DOB, phone, confidence)</th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {shown.map((p) => (
                <tr key={p.person_id} className="align-top">
                  <td className="py-2 pr-3"><div className="font-medium">{p.name}</div><div className="text-xs text-slate-500 font-mono">{p.person_id}</div></td>
                  <td className="py-2 space-y-1">
                    {p.links.map((l) => (
                      <div key={l.local_id} className="flex flex-wrap items-center gap-2 text-xs">
                        <Badge color={HOSPITAL_COLOR[l.hospital]}>{l.hospital}</Badge>
                        <span className="font-mono">{l.local_id}</span><span>{l.name}</span><span className="text-slate-500">{l.birth_date}</span>
                        <span className="text-slate-500">{l.phone || 'no phone'}</span>
                        <span className={`font-semibold ${l.confidence >= 0.95 ? 'text-emerald-600' : 'text-amber-600'}`}>{Math.round(l.confidence * 100)}%</span>
                      </div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

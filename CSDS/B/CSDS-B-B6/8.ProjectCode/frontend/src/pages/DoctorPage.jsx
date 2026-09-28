import { useState } from 'react'
import { Lock, Search, Stethoscope, UserRound } from 'lucide-react'
import api from '../api'
import { useAuth } from '../App.jsx'
import { AssistantPanel, RiskPanel, SourcesBar, Timeline } from '../components/RecordViews'
import { Badge, Button, Card, ErrorBox, HOSPITAL_COLOR, Input, Spinner } from '../components/ui'

export default function DoctorPage() {
  const { user } = useAuth()
  const [q, setQ] = useState({ name: '', birth_date: '' })
  const [search, setSearch] = useState({ loading: false, error: null, data: null })
  const [selected, setSelected] = useState(null)
  const [reason, setReason] = useState('Continuity of care')
  const [access, setAccess] = useState({ loading: false, error: null, record: null, blocked: false })

  const runSearch = async (e) => {
    e.preventDefault()
    setSearch({ loading: true, error: null, data: null })
    try {
      const { data } = await api.get('/mpi/search', { params: { q: q.name, birth_date: q.birth_date } })
      setSearch({ loading: false, error: null, data })
    } catch (err) { setSearch({ loading: false, error: err, data: null }) }
  }

  const requestAccess = async () => {
    setAccess({ loading: true, error: null, record: null, blocked: false })
    try {
      const { data } = await api.post('/access/request', { person_id: selected.person_id, reason })
      setAccess({ loading: false, error: null, record: data, blocked: false })
    } catch (err) {
      setAccess({ loading: false, error: err, record: null, blocked: err.response?.status === 403 })
    }
  }

  const pick = (p) => { setSelected(p); setAccess({ loading: false, error: null, record: null, blocked: false }) }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2"><Stethoscope className="w-6 h-6 text-teal-600" /> Patient lookup</h1>
      <div className="grid lg:grid-cols-3 gap-4">
        <Card title="Search the Master Patient Index" icon={Search}>
          <form onSubmit={runSearch} className="space-y-3">
            <Input label="Name" value={q.name} onChange={(e) => setQ({ ...q, name: e.target.value })} placeholder="e.g. Gibson" />
            <Input label="Date of birth (optional)" type="date" value={q.birth_date} onChange={(e) => setQ({ ...q, birth_date: e.target.value })} />
            <Button type="submit" loading={search.loading} className="w-full">Search</Button>
          </form>
          <div className="mt-3 space-y-2">
            <ErrorBox error={search.error} />
            {search.data?.length === 0 && <p className="text-sm text-slate-500">No matching person.</p>}
            {search.data?.map((p) => (
              <button key={p.person_id} onClick={() => pick(p)}
                className={`w-full text-left rounded-lg border p-2.5 ${selected?.person_id === p.person_id ? 'border-teal-500 bg-teal-50' : 'border-slate-200 hover:bg-slate-50'}`}>
                <div className="font-medium text-sm text-slate-800">{p.name}</div>
                <div className="text-xs text-slate-500">{p.birth_date} - {p.gender} - {p.person_id}</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {p.hospitals.map((h) => <Badge key={h.key} color={HOSPITAL_COLOR[h.key]}>{h.name.split(' ')[0]} {Math.round(h.confidence * 100)}%</Badge>)}
                </div>
              </button>
            ))}
          </div>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          {!selected && (
            <Card><p className="text-sm text-slate-500 py-8 text-center">Search for a patient, then request access to their history from other hospitals.</p></Card>
          )}
          {selected && (
            <Card title={`Access request - ${selected.name}`} icon={UserRound}>
              <div className="flex flex-wrap items-end gap-3">
                <Input label="Clinical reason" value={reason} onChange={(e) => setReason(e.target.value)} className="flex-1 min-w-48" />
                <Button loading={access.loading} onClick={requestAccess}>{access.record ? 'Refresh record' : 'Request history'}</Button>
              </div>
              <p className="text-xs text-slate-500 mt-2">Requests are checked against the patient's consent for {user.hospital_name}. Every request is written to the audit ledger.</p>
              {access.blocked && (
                <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  <Lock className="w-4 h-4 mt-0.5 shrink-0" />
                  <div><div className="font-medium">Access blocked</div>{access.error.response?.data?.detail} The request now appears in the patient's consent screen.</div>
                </div>
              )}
              {access.error && !access.blocked && <div className="mt-3"><ErrorBox error={access.error} /></div>}
            </Card>
          )}
          {access.loading && <Spinner label="Checking consent and fetching FHIR records from each hospital..." />}
          {access.record && (
            <>
              <SourcesBar record={access.record} personId={selected.person_id} />
              <RiskPanel personId={selected.person_id} />
              <Timeline items={access.record.timeline} />
              <AssistantPanel personId={selected.person_id} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

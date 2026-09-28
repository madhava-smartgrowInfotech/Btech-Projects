import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import api, { errorText, pct } from '../api.js'
import { ErrorBox, Spinner, StageBadge } from '../components/ui.jsx'

export default function Patients() {
  const [q, setQ] = useState('')
  const [patients, setPatients] = useState(null)
  const [recent, setRecent] = useState(null)
  const [error, setError] = useState('')

  const load = () => {
    setError('')
    Promise.all([api.get('/patients', { params: { q } }), api.get('/screenings', { params: { limit: 10 } })])
      .then(([p, s]) => {
        setPatients(p.data)
        setRecent(s.data)
      })
      .catch((e) => setError(errorText(e)))
  }
  useEffect(() => {
    const t = setTimeout(load, 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-900">Patients & history</h1>
        <Link to="/screening/new" className="btn-primary">New screening</Link>
      </div>
      <ErrorBox error={error} onRetry={load} />
      <div className="card">
        <div className="relative mb-4 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input className="input pl-9" placeholder="Search by name or code" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        {!patients ? <Spinner /> : patients.length === 0 ? (
          <p className="py-6 text-sm text-slate-500">No patients yet. Start a new screening to register one.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-slate-500">
                <tr><th className="py-2">Patient</th><th>Code</th><th>Age / Sex</th><th>Screenings</th><th>Last screened</th><th>Latest stage</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {patients.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="py-2"><Link className="font-medium text-teal-700 hover:underline" to={`/patients/${p.id}`}>{p.name}</Link></td>
                    <td>{p.code}</td>
                    <td>{p.age} / {p.sex}</td>
                    <td>{p.screening_count}</td>
                    <td>{p.last_screened ? new Date(p.last_screened).toLocaleDateString() : '-'}</td>
                    <td><StageBadge stage={p.latest_stage} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <div className="card">
        <h2 className="mb-3 font-semibold">Recent screenings</h2>
        {!recent ? <Spinner /> : recent.length === 0 ? <p className="text-sm text-slate-500">No screenings yet.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-slate-500">
                <tr><th className="py-2">#</th><th>Patient</th><th>Date</th><th>Retinopathy</th><th>Heart risk</th><th>Stage</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recent.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="py-2"><Link className="text-teal-700 hover:underline" to={`/screenings/${s.id}`}>#{s.id}</Link></td>
                    <td>{s.patient_name}</td>
                    <td>{new Date(s.created_at).toLocaleString()}</td>
                    <td>{pct(s.retina_prob)}</td>
                    <td>{pct(s.heart_prob)}</td>
                    <td><StageBadge stage={s.stage} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

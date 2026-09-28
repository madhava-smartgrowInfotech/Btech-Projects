import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, FileText } from 'lucide-react'
import api, { errorText, pct } from '../api.js'
import { ErrorBox, Spinner, StageBadge } from '../components/ui.jsx'

export default function PatientDetail() {
  const { id } = useParams()
  const [p, setP] = useState(null)
  const [error, setError] = useState('')
  const load = () => {
    setError('')
    api.get(`/patients/${id}`).then(({ data }) => setP(data)).catch((e) => setError(errorText(e)))
  }
  useEffect(load, [id])

  if (error) return <ErrorBox error={error} onRetry={load} />
  if (!p) return <Spinner />
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Link to="/patients" className="flex items-center gap-1 text-sm text-teal-700 hover:underline"><ArrowLeft className="h-4 w-4" /> All patients</Link>
          <h1 className="text-2xl font-bold text-slate-900">{p.name}</h1>
          <p className="text-sm text-slate-500">{p.code} - {p.age} years - {p.sex} - registered {new Date(p.created_at).toLocaleDateString()}</p>
        </div>
        <Link to={`/screening/new?patient=${p.id}`} className="btn-primary">New screening for this patient</Link>
      </div>
      <div className="card">
        <h2 className="mb-3 font-semibold">Screening history</h2>
        {p.screenings.length === 0 ? <p className="text-sm text-slate-500">No screenings yet.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-slate-500">
                <tr><th className="py-2">#</th><th>Date</th><th>Eye</th><th>Image quality</th><th>Retinopathy</th><th>Heart risk</th><th>Stage</th><th /></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {p.screenings.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="py-2"><Link className="text-teal-700 hover:underline" to={`/screenings/${s.id}`}>#{s.id}</Link></td>
                    <td>{new Date(s.created_at).toLocaleString()}</td>
                    <td>{s.eye}</td>
                    <td>{s.quality_passed ? 'Passed' : 'Check'}</td>
                    <td>{pct(s.retina_prob)}</td>
                    <td>{pct(s.heart_prob)}</td>
                    <td><StageBadge stage={s.stage} /></td>
                    <td>{s.stage && <Link to={`/screenings/${s.id}/report`} className="text-teal-700" title="Report"><FileText className="h-4 w-4" /></Link>}</td>
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

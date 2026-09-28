import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { errMsg } from '../api'
import { ErrorBox, Spinner, GradeBadge } from '../components/ui'

export default function Scans() {
  const [scans, setScans] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/scans').then((r) => setScans(r.data)).catch((e) => setError(errMsg(e)))
  }, [])

  if (error) return <ErrorBox message={error} />
  if (scans === null) return <Spinner />

  return (
    <div>
      <h1 className="text-2xl font-extrabold mb-1">Scans</h1>
      <p className="text-slate-500 text-sm mb-5">All security scans you have run.</p>
      {scans.length === 0 ? (
        <div className="text-slate-500">No scans yet. Start one from the Targets page.</div>
      ) : (
        <div className="card divide-y divide-slate-100">
          {scans.map((s) => (
            <button key={s.id} onClick={() => navigate(`/app/scans/${s.id}`)}
              className="w-full flex items-center gap-4 px-4 py-3 hover:bg-slate-50 text-left">
              <span className="text-slate-400 font-mono text-sm w-10">#{s.id}</span>
              <span className="font-semibold flex-1">{s.target_name}</span>
              <StatusPill status={s.status} progress={s.progress} />
              {s.status === 'done' && (
                <span className="flex items-center gap-2">
                  <span className="font-bold">{s.score}/100</span>
                  <GradeBadge grade={s.grade} />
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function StatusPill({ status, progress }) {
  const map = {
    done: 'bg-green-50 text-green-700 border-green-200',
    running: 'bg-blue-50 text-blue-700 border-blue-200',
    pending: 'bg-slate-50 text-slate-600 border-slate-200',
    error: 'bg-red-50 text-red-700 border-red-200',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-1 rounded-full border ${map[status] || map.pending}`}>
      {status === 'running' ? `running ${progress}%` : status}
    </span>
  )
}

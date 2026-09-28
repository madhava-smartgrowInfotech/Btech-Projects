import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Activity, Loader2 } from 'lucide-react'
import api, { errorMessage } from '../api'
import { ErrorBox } from '../components/ui'

const DEMO = [
  { role: 'Administrator', email: 'admin@hospisense.app', password: 'Admin@123' },
  { role: 'Doctor', email: 'doctor@hospisense.app', password: 'Doctor@123' },
]

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/auth/login', { email, password })
      onLogin(data)
      navigate('/dashboard')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <Link to="/" className="flex items-center justify-center gap-2 text-xl font-semibold text-slate-900 mb-6">
          <Activity className="text-teal-700" /> HospiSense
        </Link>
        <form onSubmit={submit} className="card p-6 space-y-4">
          <h1 className="text-lg font-semibold text-slate-900">Sign in</h1>
          <ErrorBox message={error} />
          <div>
            <label className="label" htmlFor="email">Email</label>
            <input id="email" className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
          </div>
          <div>
            <label className="label" htmlFor="password">Password</label>
            <input id="password" className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
          </div>
          <button className="btn-primary w-full" disabled={loading}>
            {loading && <Loader2 size={16} className="animate-spin" />} Sign in
          </button>
        </form>
        <div className="card p-4 mt-4">
          <div className="text-xs font-medium text-slate-500 mb-2">Demo accounts</div>
          <div className="grid grid-cols-2 gap-2">
            {DEMO.map((d) => (
              <button
                key={d.email}
                type="button"
                className="btn-secondary text-xs"
                onClick={() => {
                  setEmail(d.email)
                  setPassword(d.password)
                }}
              >
                {d.role}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

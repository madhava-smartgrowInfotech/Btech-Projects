import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Droplets, Loader2 } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { errorText } from '../api'
import { ErrorBox } from '../components/ui.jsx'

const DEMO = [
  { role: 'Engineer', email: 'engineer@aquavision.local', password: 'engineer123' },
  { role: 'Manager', email: 'manager@aquavision.local', password: 'manager123' },
]

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState(DEMO[0].email)
  const [password, setPassword] = useState(DEMO[0].password)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  if (user) return <Navigate to="/dashboard" replace />

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email, password)
      nav('/dashboard')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-sky-50 to-white px-4">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2 text-sky-700 font-semibold text-xl mb-6">
          <Droplets className="w-7 h-7" /> AquaVision
        </Link>
        <form onSubmit={submit} className="card p-6 space-y-4">
          <h1 className="text-lg font-semibold text-slate-900">Sign in</h1>
          <div>
            <label className="label" htmlFor="email">Email</label>
            <input id="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
          </div>
          <div>
            <label className="label" htmlFor="password">Password</label>
            <input id="password" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
          </div>
          <ErrorBox error={error} />
          <button className="btn-primary w-full" disabled={busy}>
            {busy && <Loader2 className="w-4 h-4 animate-spin" />} Sign in
          </button>
          <div className="border-t border-slate-100 pt-4">
            <div className="text-xs text-slate-500 mb-2">Demo accounts</div>
            <div className="flex gap-2">
              {DEMO.map((d) => (
                <button
                  type="button"
                  key={d.role}
                  className="btn-secondary flex-1"
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
        </form>
      </div>
    </div>
  )
}

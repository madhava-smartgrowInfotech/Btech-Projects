import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api.js'
import { homeFor, useAuth } from '../auth.jsx'
import { Logo } from '../components/Layout.jsx'
import { ErrorBox, Spinner } from '../components/ui.jsx'

const DEMO = [
  { role: 'Citizen', email: 'citizen@civicpulse.local', password: 'Citizen@123' },
  { role: 'Officer', email: 'officer@civicpulse.local', password: 'Officer@123' },
  { role: 'Admin', email: 'admin@civicpulse.local', password: 'Admin@123' },
]

export default function Login() {
  const { user, login, register } = useAuth()
  const nav = useNavigate()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  if (user) return <Navigate to={homeFor(user)} replace />

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const u = mode === 'login' ? await login(form.email, form.password) : await register(form.name, form.email, form.password)
      nav(homeFor(u))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 flex justify-center">
          <Logo />
        </div>
        <div className="card p-6">
          <div className="mb-5 grid grid-cols-2 rounded-lg bg-slate-100 p-1 text-sm font-medium">
            {[
              ['login', 'Log in'],
              ['register', 'Create citizen account'],
            ].map(([m, label]) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m)
                  setError('')
                }}
                className={`rounded-md py-1.5 ${mode === m ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'}`}
              >
                {label}
              </button>
            ))}
          </div>
          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="label" htmlFor="name">Full name</label>
                <input id="name" className="input" value={form.name} onChange={set('name')} required autoComplete="name" />
              </div>
            )}
            <div>
              <label className="label" htmlFor="email">Email</label>
              <input id="email" type="email" className="input" value={form.email} onChange={set('email')} required autoComplete="email" />
            </div>
            <div>
              <label className="label" htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                className="input"
                value={form.password}
                onChange={set('password')}
                required
                minLength={mode === 'register' ? 8 : undefined}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
            </div>
            <ErrorBox message={error} />
            <button className="btn-primary w-full" disabled={busy}>
              {busy && <Spinner />} {mode === 'login' ? 'Log in' : 'Create account'}
            </button>
          </form>
        </div>
        {mode === 'login' && (
          <div className="card mt-4 p-4">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Demo accounts</div>
            <div className="grid grid-cols-3 gap-2">
              {DEMO.map((d) => (
                <button
                  key={d.role}
                  type="button"
                  className="btn-secondary px-2 py-1.5 text-xs"
                  onClick={() => setForm({ ...form, email: d.email, password: d.password })}
                >
                  {d.role}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-slate-500">Click a role to fill in its credentials, then log in.</p>
          </div>
        )}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Building2, LayoutDashboard, LogIn, User } from 'lucide-react'
import { errMsg } from '../api'
import { homeFor, useAuth } from '../auth'
import { ErrorBox } from '../components/ui'

const DEMOS = [
  ['patient', User, 'Patient', 'patient@mediqueue.app'],
  ['staff', Building2, 'Hospital staff', 'desk1@mediqueue.app'],
  ['admin', LayoutDashboard, 'District admin', 'admin@mediqueue.app'],
]

export default function Login() {
  const { login, register } = useAuth()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({
    email: params.get('role') === 'staff' ? 'desk1@mediqueue.app' : '',
    password: '',
    name: '',
    age: '',
    gender: '',
    phone: '',
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e?.preventDefault()
    setBusy(true)
    setError('')
    try {
      const u =
        mode === 'login'
          ? await login(form.email, form.password)
          : await register({
              name: form.name,
              email: form.email,
              password: form.password,
              age: form.age ? Number(form.age) : null,
              gender: form.gender || null,
              phone: form.phone || null,
            })
      nav(homeFor(u))
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }

  const demo = async (email) => {
    setBusy(true)
    setError('')
    try {
      nav(homeFor(await login(email, 'demo1234')))
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-md mx-auto space-y-4">
      <div className="card p-6">
        <div className="flex rounded-lg bg-slate-100 p-1 mb-5">
          {['login', 'register'].map((m) => (
            <button
              key={m}
              className={`flex-1 rounded-md py-1.5 text-sm font-medium ${mode === m ? 'bg-white shadow text-teal-800' : 'text-slate-500'}`}
              onClick={() => setMode(m)}
            >
              {m === 'login' ? 'Log in' : 'Create patient account'}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="space-y-3">
          {mode === 'register' && (
            <>
              <div>
                <label className="label">Full name</label>
                <input className="input" value={form.name} onChange={set('name')} required minLength={2} />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="label">Age</label>
                  <input className="input" type="number" min="0" max="120" value={form.age} onChange={set('age')} />
                </div>
                <div>
                  <label className="label">Gender</label>
                  <select className="input" value={form.gender} onChange={set('gender')}>
                    <option value="">-</option>
                    <option value="F">Female</option>
                    <option value="M">Male</option>
                  </select>
                </div>
                <div>
                  <label className="label">Phone</label>
                  <input className="input" value={form.phone} onChange={set('phone')} />
                </div>
              </div>
            </>
          )}
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={form.email} onChange={set('email')} required autoComplete="username" />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              value={form.password}
              onChange={set('password')}
              required
              minLength={mode === 'register' ? 6 : 1}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>
          <ErrorBox error={error} />
          <button className="btn-primary w-full" disabled={busy}>
            <LogIn className="h-4 w-4" /> {busy ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Create account'}
          </button>
        </form>
      </div>

      <div className="card p-5">
        <div className="text-sm font-semibold mb-1">Demo accounts</div>
        <p className="text-xs text-slate-500 mb-3">
          Password <code className="bg-slate-100 px-1 rounded">demo1234</code>. Each hospital has an OP desk login{' '}
          <code className="bg-slate-100 px-1 rounded">desk&lt;id&gt;@mediqueue.app</code>.
        </p>
        <div className="grid grid-cols-3 gap-2">
          {DEMOS.map(([key, Icon, label, email]) => (
            <button key={key} className="btn-outline flex-col !py-3" disabled={busy} onClick={() => demo(email)}>
              <Icon className="h-5 w-5 text-teal-700" />
              <span className="text-xs">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

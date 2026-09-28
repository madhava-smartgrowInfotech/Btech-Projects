import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import api from '../api'
import { useAuth } from '../App'
import { ErrorBox, useAction } from '../components/ui'

const DEMO = [
  ['candidate', 'Candidate', 'candidate@talenttrack.dev'],
  ['recruiter', 'Recruiter', 'recruiter@talenttrack.dev'],
  ['career', 'Career services', 'career@talenttrack.dev'],
  ['expert', 'Expert interviewer', 'expert@talenttrack.dev'],
]

export default function Login() {
  const [params] = useSearchParams()
  const { login } = useAuth()
  const [mode, setMode] = useState(params.get('mode') === 'register' ? 'register' : 'login')
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'candidate' })
  const { busy, error, run } = useAction()
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = (e) => {
    e.preventDefault()
    run(async () => {
      const url = mode === 'login' ? '/auth/login' : '/auth/register'
      const body = mode === 'login' ? { email: form.email, password: form.password } : form
      const r = await api.post(url, body)
      login(r.data.token, r.data.user)
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10 bg-slate-50">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2 font-bold text-slate-900 text-xl mb-6">
          <span className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center">T</span> TalentTrack
        </Link>
        <div className="card p-6">
          <div className="grid grid-cols-2 gap-1 bg-slate-100 rounded-lg p-1 mb-5">
            {['login', 'register'].map((m) => (
              <button key={m} onClick={() => setMode(m)}
                className={`py-1.5 rounded-md text-sm font-medium ${mode === m ? 'bg-white shadow text-slate-900' : 'text-slate-500'}`}>
                {m === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>
          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && (
              <>
                <div>
                  <label className="label">Full name</label>
                  <input className="input" value={form.name} onChange={set('name')} required />
                </div>
                <div>
                  <label className="label">I am a</label>
                  <select className="input" value={form.role} onChange={set('role')}>
                    <option value="candidate">Candidate preparing for jobs</option>
                    <option value="recruiter">Recruiter running hiring drives</option>
                  </select>
                </div>
              </>
            )}
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" value={form.email} onChange={set('email')} required />
            </div>
            <div>
              <label className="label">Password</label>
              <input className="input" type="password" value={form.password} onChange={set('password')} required minLength={6} />
            </div>
            <ErrorBox error={error} />
            <button className="btn-primary w-full" disabled={busy}>
              {busy && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </div>
        <div className="card p-4 mt-4">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Demo accounts (password Demo@123)</div>
          <div className="grid grid-cols-2 gap-2">
            {DEMO.map(([role, label, email]) => (
              <button key={role} className="btn-secondary !justify-start text-left"
                onClick={() => { setMode('login'); setForm({ ...form, email, password: 'Demo@123' }) }}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

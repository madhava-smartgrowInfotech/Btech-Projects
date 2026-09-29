import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import api, { errMsg } from '../api.js'
import { ErrorBox } from '../components/ui.jsx'

const DEMO = { email: 'demo@carewatch.app', password: 'CareWatch123' }

export default function Login() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState(params.get('demo') ? { name: '', ...DEMO } : { name: '', email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post(mode === 'login' ? '/auth/login' : '/auth/register', form)
      localStorage.setItem('cw_token', data.token)
      localStorage.setItem('cw_user', JSON.stringify(data.user))
      nav('/monitor')
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-teal-50 to-white px-4">
      <div className="card w-full max-w-sm p-7">
        <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900 text-lg mb-6">
          <img src="/favicon.svg" className="w-8 h-8" alt="" /> CareWatch
        </Link>
        <div className="grid grid-cols-2 bg-slate-100 rounded-lg p-1 mb-5 text-sm">
          {['login', 'register'].map((m) => (
            <button key={m} onClick={() => { setMode(m); setError('') }}
              className={`rounded-md py-1.5 ${mode === m ? 'bg-white shadow-sm font-medium' : 'text-slate-600'}`}>
              {m === 'login' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="space-y-4">
          {mode === 'register' && (
            <div><label className="label">Your name</label><input className="input" value={form.name} onChange={set('name')} required /></div>
          )}
          <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={set('email')} required /></div>
          <div><label className="label">Password</label><input className="input" type="password" value={form.password} onChange={set('password')} required minLength={6} /></div>
          <ErrorBox error={error} />
          <button className="btn btn-primary w-full" disabled={busy}>
            {busy && <Loader2 className="w-4 h-4 animate-spin" />} {mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
        <div className="mt-5 rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600">
          Demo account: <b>{DEMO.email}</b> / <b>{DEMO.password}</b>
          <button className="ml-2 text-teal-700 underline" onClick={() => { setMode('login'); setForm({ name: '', ...DEMO }) }}>Fill in</button>
        </div>
      </div>
    </div>
  )
}

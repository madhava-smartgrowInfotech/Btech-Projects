import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LockKeyhole } from 'lucide-react'
import api, { errMsg } from '../api'
import { ErrorBox, Spinner } from '../components/ui'

export default function Login({ onAuth }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: 'demo@skycipher.app', password: 'SkyCipher@2026' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = mode === 'login' ? { email: form.email, password: form.password } : form
      onAuth((await api.post(`/auth/${mode}`, body)).data)
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900 px-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl bg-white p-6 shadow-xl">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <LockKeyhole className="h-5 w-5 text-sky-600" /> SkyCipher
        </Link>
        <div className="flex rounded-lg bg-slate-100 p-1 text-sm">
          {['login', 'register'].map((m) => (
            <button type="button" key={m} onClick={() => { setMode(m); setError('') }}
              className={`flex-1 rounded-md py-1.5 ${mode === m ? 'bg-white font-medium shadow' : 'text-slate-500'}`}>
              {m === 'login' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>
        {mode === 'register' && (
          <div><label className="label">Name</label><input className="input" value={form.name} onChange={set('name')} required /></div>
        )}
        <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={set('email')} required /></div>
        <div><label className="label">Password</label><input className="input" type="password" value={form.password} onChange={set('password')} required minLength={6} /></div>
        <ErrorBox error={error} />
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? <Spinner label="Please wait..." /> : mode === 'login' ? 'Sign in' : 'Create account'}
        </button>
        {mode === 'login' && <p className="text-center text-xs text-slate-500">Demo account is pre-filled.</p>}
      </form>
    </div>
  )
}

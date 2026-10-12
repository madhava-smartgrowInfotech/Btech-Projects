import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import api, { errText, setSession } from '../api'
import { ErrorBox, Spinner } from '../components/ui'

export default function Login() {
  const nav = useNavigate()
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('Demo@12345')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post(`/auth/${mode}`, { username, password })
      setSession(data.token, data.username)
      nav('/keys')
    } catch (err) {
      setError(errText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-ink-900">
          <ShieldCheck className="h-6 w-6 text-brand-600" /> CipherVeil
        </Link>
        <h2>{mode === 'login' ? 'Sign in' : 'Create an account'}</h2>
        <div>
          <label className="label" htmlFor="u">Username</label>
          <input id="u" className="input" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required minLength={3} />
        </div>
        <div>
          <label className="label" htmlFor="p">Password</label>
          <input id="p" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={8} />
          {mode === 'register' && <p className="mt-1 text-xs text-slate-500">At least 8 characters.</p>}
        </div>
        <ErrorBox>{error}</ErrorBox>
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? <Spinner text="Please wait..." /> : mode === 'login' ? 'Sign in' : 'Create account'}
        </button>
        <button type="button" className="w-full text-center text-sm text-brand-700 hover:underline"
          onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
          {mode === 'login' ? 'New here? Create an account' : 'Have an account? Sign in'}
        </button>
        {mode === 'login' && <p className="text-center text-xs text-slate-400">Demo login is filled in: demo / Demo@12345</p>}
      </form>
    </div>
  )
}

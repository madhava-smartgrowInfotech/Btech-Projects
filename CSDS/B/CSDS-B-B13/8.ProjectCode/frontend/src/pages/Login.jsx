import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { useAuth } from '../auth'
import { errMsg } from '../api'
import { ErrorBox } from '../components/ui'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('demo@apisentry.local')
  const [password, setPassword] = useState('demo12345')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(''); setBusy(true)
    try {
      await login(email, password, mode === 'register')
      navigate('/app/targets')
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 font-extrabold text-2xl mb-6">
          <ShieldCheck className="text-brand-500" /> APISentry
        </div>
        <div className="card p-6">
          <div className="flex gap-2 mb-5">
            {['login', 'register'].map((m) => (
              <button key={m} onClick={() => setMode(m)}
                className={`flex-1 py-2 rounded-lg font-semibold capitalize ${
                  mode === m ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                {m === 'login' ? 'Sign in' : 'Register'}
              </button>
            ))}
          </div>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input className="input" value={email} onChange={(e) => setEmail(e.target.value)}
                autoComplete="username" />
            </div>
            <div>
              <label className="label">Password</label>
              <input className="input" type="password" value={password}
                onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
            </div>
            <ErrorBox message={error} />
            <button className="btn-primary w-full py-2.5" disabled={busy}>
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
          <p className="text-xs text-slate-500 mt-4 text-center">
            Demo login is pre-filled: <b>demo@apisentry.local</b> / <b>demo12345</b>
          </p>
        </div>
      </div>
    </div>
  )
}

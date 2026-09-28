import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api, { errorMessage } from '../api'
import { useAuth } from '../App'
import { Logo } from '../components/Layout'
import { ErrorBox } from '../components/ui'

const DEMO = { email: 'demo@taxsentinel.app', password: 'Demo@1234' }

export default function Login() {
  const [params] = useSearchParams()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState(params.get('demo') ? { name: '', ...DEMO } : { name: '', email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const { signIn } = useAuth()
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const body = mode === 'login' ? { email: form.email, password: form.password } : form
      const { data } = await api.post(`/auth/${mode}`, body)
      signIn(data.token, data.user)
      navigate('/app')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const field = (key, label, type = 'text', extra = {}) => (
    <label className="block">
      <span className="text-sm text-slate-700">{label}</span>
      <input type={type} value={form[key]} required onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100" {...extra} />
    </label>
  )

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm">
        <Link to="/" className="flex justify-center mb-6"><Logo /></Link>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex rounded-lg bg-slate-100 p-1 mb-5 text-sm">
            {['login', 'register'].map((m) => (
              <button key={m} onClick={() => { setMode(m); setError(null) }}
                className={`flex-1 rounded-md py-1.5 ${mode === m ? 'bg-white shadow-sm font-medium text-slate-900' : 'text-slate-500'}`}>
                {m === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>
          <form onSubmit={submit} className="space-y-3">
            {mode === 'register' && field('name', 'Full name')}
            {field('email', 'Email', 'email')}
            {field('password', 'Password', 'password', { minLength: mode === 'register' ? 8 : undefined })}
            <ErrorBox error={error} />
            <button disabled={busy} className="w-full flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-indigo-300">
              {busy && <Loader2 size={16} className="animate-spin" />}
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
          {mode === 'login' && (
            <button onClick={() => setForm({ ...form, ...DEMO })} className="mt-4 w-full rounded-lg border border-dashed border-slate-300 p-2.5 text-left text-xs text-slate-600 hover:bg-slate-50">
              Demo account: <b>{DEMO.email}</b> / <b>{DEMO.password}</b> <span className="text-indigo-600">(click to fill)</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

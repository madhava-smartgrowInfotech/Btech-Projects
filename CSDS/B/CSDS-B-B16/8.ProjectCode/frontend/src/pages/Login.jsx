import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, Loader2 } from 'lucide-react'
import api, { errorText } from '../api.js'
import { ErrorBox } from '../components/ui.jsx'

const DEMO = [
  ['clinician@retinaguard.local', 'Clinician'],
  ['technician@retinaguard.local', 'Technician'],
]

export default function Login() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('rg_token', data.token)
      localStorage.setItem('rg_user', JSON.stringify(data.user))
      nav('/screening/new')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-teal-50 to-slate-50 px-4">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-6 flex items-center justify-center gap-2 text-xl font-bold text-teal-800">
          <Eye className="h-7 w-7" /> RetinaGuard
        </Link>
        <form onSubmit={submit} className="card space-y-4">
          <h1 className="text-lg font-semibold">Sign in</h1>
          <div>
            <label className="label" htmlFor="email">Email</label>
            <input id="email" type="email" className="input" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="password">Password</label>
            <input id="password" type="password" className="input" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <ErrorBox error={error} />
          <button className="btn-primary w-full" disabled={loading}>
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Sign in
          </button>
          <div className="border-t border-slate-100 pt-3 text-xs text-slate-500">
            Demo accounts (password in README):
            <div className="mt-2 flex gap-2">
              {DEMO.map(([e, r]) => (
                <button type="button" key={e} className="btn-secondary flex-1 px-2 py-1 text-xs" onClick={() => setEmail(e)}>
                  {r}
                </button>
              ))}
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

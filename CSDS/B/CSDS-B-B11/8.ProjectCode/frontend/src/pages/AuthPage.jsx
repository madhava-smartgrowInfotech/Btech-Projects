import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Leaf, Loader2 } from 'lucide-react'
import { useAuth } from '../auth'
import { errorMessage } from '../api'
import { ErrorBox } from '../components/ui'

export default function AuthPage({ mode }) {
  const isLogin = mode === 'login'
  const { login, register } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const u = isLogin ? await login(form.email, form.password) : await register(form.name, form.email, form.password)
      nav(u.has_profile ? '/dashboard' : '/profile')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-emerald-50 to-white px-4">
      <div className="card w-full max-w-sm p-6">
        <Link to="/" className="flex items-center gap-2 font-semibold text-emerald-700 mb-6"><Leaf className="h-5 w-5" /> NutriSense</Link>
        <h1 className="text-xl font-semibold text-slate-800">{isLogin ? 'Welcome back' : 'Create your account'}</h1>
        <form onSubmit={submit} className="mt-5 space-y-4">
          {!isLogin && (
            <div><label className="label">Name</label><input className="input" value={form.name} onChange={set('name')} required /></div>
          )}
          <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={set('email')} required /></div>
          <div><label className="label">Password</label><input className="input" type="password" value={form.password} onChange={set('password')} required minLength={6} /></div>
          <ErrorBox message={error} />
          <button className="btn-primary w-full" disabled={busy}>
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}{isLogin ? 'Log in' : 'Create account'}
          </button>
        </form>
        {isLogin && (
          <div className="mt-4 rounded-xl bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600">
            <strong>Sample account:</strong> demo@nutrisense.app / Demo@1234
            <button type="button" className="ml-2 text-emerald-700 underline" onClick={() => setForm({ ...form, email: 'demo@nutrisense.app', password: 'Demo@1234' })}>Fill in</button>
          </div>
        )}
        <p className="mt-4 text-sm text-slate-600 text-center">
          {isLogin ? <>New here? <Link to="/register" className="text-emerald-700 font-medium">Create an account</Link></>
            : <>Already have an account? <Link to="/login" className="text-emerald-700 font-medium">Log in</Link></>}
        </p>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { errorText } from '../api'
import { useAuth } from '../auth.jsx'
import Logo from '../components/Logo.jsx'
import { ErrorBox } from '../components/ui.jsx'

export default function Login({ mode }) {
  const isRegister = mode === 'register'
  const { login, register } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ name: '', email: isRegister ? '' : 'demo@signbridge.app', password: isRegister ? '' : 'demo1234' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (isRegister) await register(form.name, form.email, form.password)
      else await login(form.email, form.password)
      nav('/app')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen grid place-items-center px-4 bg-slate-50">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-6"><Logo to="/" /></div>
        <form onSubmit={submit} className="card p-6 space-y-4">
          <h1 className="text-xl font-semibold">{isRegister ? 'Create your account' : 'Sign in'}</h1>
          {isRegister && (
            <label className="block text-sm">Name<input className="input mt-1" value={form.name} onChange={set('name')} required /></label>
          )}
          <label className="block text-sm">Email<input className="input mt-1" type="email" value={form.email} onChange={set('email')} required /></label>
          <label className="block text-sm">Password<input className="input mt-1" type="password" value={form.password} onChange={set('password')} required minLength={isRegister ? 6 : 1} /></label>
          <ErrorBox error={error} />
          <button className="btn-primary w-full" disabled={busy}>
            {busy && <Loader2 size={16} className="animate-spin" />} {isRegister ? 'Create account' : 'Sign in'}
          </button>
          {!isRegister && <p className="text-xs text-slate-500 text-center">Demo account is pre-filled: demo@signbridge.app / demo1234</p>}
        </form>
        <p className="text-sm text-center mt-4 text-slate-600">
          {isRegister ? <>Already have an account? <Link className="text-indigo-600" to="/login">Sign in</Link></>
            : <>New here? <Link className="text-indigo-600" to="/register">Create an account</Link></>}
        </p>
      </div>
    </div>
  )
}

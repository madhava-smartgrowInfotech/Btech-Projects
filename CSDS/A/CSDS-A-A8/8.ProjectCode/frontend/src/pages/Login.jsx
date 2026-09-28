import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Layout.jsx'
import { ErrorBox, Spinner } from '../components/Ui.jsx'
import api, { errorText, setSession } from '../api.js'

export default function Login() {
  const nav = useNavigate()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const body = mode === 'login' ? { email: form.email, password: form.password } : form
      const { data } = await api.post(`/auth/${mode}`, body)
      setSession(data)
      nav('/mri')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex justify-center"><Logo /></div>
        <form onSubmit={submit} className="card space-y-4">
          <h1 className="text-lg font-semibold text-slate-900">{mode === 'login' ? 'Sign in' : 'Create an account'}</h1>
          {mode === 'register' && (
            <div><label className="label">Name</label><input className="input" value={form.name} onChange={set('name')} required /></div>
          )}
          <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={set('email')} required /></div>
          <div><label className="label">Password</label><input className="input" type="password" value={form.password} onChange={set('password')} required minLength={6} /></div>
          <ErrorBox error={error} />
          <button className="btn w-full" disabled={loading}>{loading ? <Spinner text="Please wait..." /> : mode === 'login' ? 'Sign in' : 'Create account'}</button>
          <button type="button" className="w-full text-sm text-teal-700 hover:underline"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
            {mode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}
          </button>
          {mode === 'login' && (
            <button type="button" className="w-full rounded-lg bg-slate-100 py-2 text-xs text-slate-600 hover:bg-slate-200"
              onClick={() => setForm({ ...form, email: 'demo@biosight.app', password: 'Demo@1234' })}>
              Use demo account (demo@biosight.app / Demo@1234)
            </button>
          )}
        </form>
      </div>
    </div>
  )
}

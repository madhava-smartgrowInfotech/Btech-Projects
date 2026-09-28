import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { HeartPulse } from 'lucide-react'
import api from '../api'
import { useAuth, HOME } from '../App.jsx'
import { Button, ErrorBox, Input } from '../components/ui'

const DEMO = [
  { label: 'Patient', username: 'patient', hint: 'records at all three hospitals' },
  { label: 'Doctor (Riverside)', username: 'dr.riverside', hint: 'Riverside Medical Center' },
  { label: 'Records staff (Lakeview)', username: 'staff.lakeview', hint: 'hospital console' },
  { label: 'Administrator', username: 'admin', hint: 'hospitals, MPI, audit' },
]

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      const { data } = await api.post('/auth/login', form)
      login(data.token, data.user)
      nav(HOME[data.user.role])
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-teal-50 to-white px-4">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2 font-bold text-xl text-slate-900 mb-6"><HeartPulse className="w-7 h-7 text-teal-600" /> UniHealth</Link>
        <form onSubmit={submit} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h1 className="text-lg font-semibold text-slate-900">Sign in</h1>
          <ErrorBox error={error} />
          <Input label="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoFocus required />
          <Input label="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <Button type="submit" loading={loading} className="w-full">Sign in</Button>
        </form>
        <div className="mt-4 bg-white rounded-xl border border-slate-200 p-4">
          <div className="text-sm font-medium text-slate-700 mb-2">Demo accounts (password <code className="bg-slate-100 px-1 rounded">demo123</code>)</div>
          <div className="grid grid-cols-2 gap-2">
            {DEMO.map((d) => (
              <button key={d.username} type="button" onClick={() => setForm({ username: d.username, password: 'demo123' })}
                className="text-left rounded-lg border border-slate-200 hover:border-teal-400 hover:bg-teal-50 px-3 py-2">
                <div className="text-sm font-medium text-slate-800">{d.label}</div>
                <div className="text-xs text-slate-500">{d.hint}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

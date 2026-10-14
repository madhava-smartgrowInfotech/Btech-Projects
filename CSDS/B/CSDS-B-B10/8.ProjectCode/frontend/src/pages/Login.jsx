import { LogIn, UserPlus } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import api, { describeError } from '../api'
import Backdrop from '../components/reactbits/Backdrop'
import { SlideUp } from '../components/motion'
import { Button, Input } from '../components/ui/controls'
import { Card } from '../components/ui/display'
import { ErrorState, useToast } from '../components/ui/feedback'
import Logo from '../components/ui/Logo'
import { Tabs } from '../components/ui/nav'
import { useAuth } from '../lib/auth'

// The demo account from the README. Pre-filled, as in the original sign-in page.
const DEMO = { email: 'demo@skycipher.app', password: 'SkyCipher@2026' }

export default function Login() {
  const { user, signIn } = useAuth()
  const location = useLocation()
  const toast = useToast()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: DEMO.email, password: DEMO.password })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  if (user) return <Navigate to={location.state?.from || '/studio'} replace />

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const body = mode === 'login' ? { email: form.email, password: form.password } : form
      const r = await api.post(`/auth/${mode}`, body)
      signIn(r.data)
      toast({ tone: 'ok', title: mode === 'login' ? 'Signed in' : 'Account created', body: `welcome, ${r.data.user.name}` })
    } catch (err) {
      setError(describeError(err, mode === 'login' ? 'Sign-in failed' : 'Could not create the account'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Backdrop intensity={0.4} className="fixed inset-0 z-0 fade-mask opacity-60" />
      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-4 py-10">
        <Link to="/" className="mb-8 self-start"><Logo /></Link>
        <SlideUp>
          <Card title={mode === 'login' ? 'Sign in' : 'Create account'} eyebrow="SkyCipher">
            <Tabs id="auth" label="Account" value={mode} onChange={(m) => { setMode(m); setError(null) }}
              tabs={[{ id: 'login', label: 'Sign in' }, { id: 'register', label: 'Create account' }]} />
            <form onSubmit={submit} className="mt-5 space-y-4" noValidate>
              {mode === 'register' && (
                <Input id="name" label="Name" autoComplete="name" value={form.name} onChange={set('name')} required />
              )}
              <Input id="email" type="email" label="Email" autoComplete="email" value={form.email} onChange={set('email')} required />
              <Input id="password" type="password" label="Password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                value={form.password} onChange={set('password')} required minLength={mode === 'register' ? 6 : undefined}
                hint={mode === 'register' ? 'At least 6 characters.' : undefined} />
              {error && <ErrorState error={error} />}
              <Button type="submit" size="lg" className="w-full" loading={busy}
                icon={mode === 'login' ? LogIn : UserPlus}>
                {mode === 'login' ? 'Sign in' : 'Create account'}
              </Button>
            </form>
            {mode === 'login' && (
              <p className="mt-4 text-xs text-muted">
                The demo account is filled in. Create your own account to keep a separate history of jobs and reports.
              </p>
            )}
          </Card>
        </SlideUp>
      </div>
    </div>
  )
}

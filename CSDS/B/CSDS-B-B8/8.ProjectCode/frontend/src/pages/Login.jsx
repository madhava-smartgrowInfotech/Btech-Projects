import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LogIn, Moon, Sun, UserPlus } from 'lucide-react'
import { BrandMark, Button, Card, IconButton, Input, Tabs } from '../components/ui'
import { FadeIn } from '../components/motion'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'
import { useToast } from '../components/ui'

const DEMO = { email: 'demo@carewatch.app', password: 'CareWatch123' }

export default function Login() {
  const { user, signIn } = useAuth()
  const { theme, toggle } = useTheme()
  const toast = useToast()
  const nav = useNavigate()
  const loc = useLocation()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    document.title = 'Sign in · CareWatch'
  }, [])

  if (user) return <Navigate to={loc.state?.from?.startsWith('/app') ? loc.state.from : '/app/monitor'} replace />

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const u = await signIn(mode, mode === 'login' ? { email: form.email, password: form.password } : form)
      toast({ title: mode === 'login' ? `Welcome back, ${u.name}` : 'Account created', message: 'You are signed in.' })
      nav('/app/monitor', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }
  const demo = () => {
    setMode('login')
    setForm({ ...form, ...DEMO })
  }

  return (
    <div className="landing auth-page">
      <div className="hero-layer hero-grid" aria-hidden="true" />
      <div className="hero-layer hero-orbs" aria-hidden="true">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
      </div>
      <div className="auth-links">
        <Link to="/" className="brand" style={{ padding: 0 }}>
          <BrandMark />
          <span>CareWatch</span>
        </Link>
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
      </div>
      <FadeIn style={{ width: '100%', display: 'grid', placeItems: 'center' }}>
        <Card className="auth-card" spotlight={false}>
          <Tabs
            label="Sign in or create an account"
            value={mode}
            onChange={(v) => {
              setMode(v)
              setError('')
            }}
            tabs={[
              { value: 'login', label: 'Sign in', icon: LogIn },
              { value: 'register', label: 'Create account', icon: UserPlus },
            ]}
          />
          <h1>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
          <p className="muted">{mode === 'login' ? 'Sign in to see the live monitor, alerts and reports.' : 'Set up CareWatch for the person you look after.'}</p>
          <form onSubmit={submit} className="stack" style={{ marginTop: 22, gap: 14 }} noValidate={false}>
            {mode === 'register' && (
              <Input label="Your name" value={form.name} onChange={set('name')} required autoComplete="name" data-autofocus />
            )}
            <Input label="Email" type="email" value={form.email} onChange={set('email')} required autoComplete="email" />
            <Input
              label="Password"
              type="password"
              value={form.password}
              onChange={set('password')}
              required
              minLength={mode === 'register' ? 6 : undefined}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              hint={mode === 'register' ? 'At least 6 characters.' : undefined}
            />
            {error && (
              <p className="field-error" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" variant="primary" size="lg" loading={busy}>
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
            {mode === 'login' && (
              <Button variant="ghost" onClick={demo}>
                Fill in the demo account
              </Button>
            )}
          </form>
        </Card>
      </FadeIn>
    </div>
  )
}

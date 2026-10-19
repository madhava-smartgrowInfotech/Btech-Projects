import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LogIn, Moon, ShieldCheck, Sun, UserPlus, Zap } from 'lucide-react'
import { BrandMark, Button, Card, IconButton, Input, Tabs, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'

const DEMOS = [
  { label: 'Driver demo', email: 'driver1@parksure.app', password: 'driver123', icon: Zap },
  { label: 'Admin demo', email: 'admin@parksure.app', password: 'admin123', icon: ShieldCheck },
]

export default function Login() {
  const { user, login, register } = useAuth()
  const { theme, toggle } = useTheme()
  const toast = useToast()
  const nav = useNavigate()
  const loc = useLocation()
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [fieldErr, setFieldErr] = useState({})

  const dest = (u) => (loc.state?.from && loc.state.from.startsWith('/app') ? loc.state.from : u.role === 'admin' ? '/app/admin' : '/app/find')
  if (user && !busy) return <Navigate to={dest(user)} replace />

  const validate = () => {
    const e = {}
    if (mode === 'register' && name.trim().length < 2) e.name = 'Enter your name (at least 2 characters).'
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) e.email = 'Enter a valid email address.'
    if (!password) e.password = 'Enter your password.'
    else if (mode === 'register' && password.length < 6) e.password = 'Use at least 6 characters.'
    setFieldErr(e)
    return Object.keys(e).length === 0
  }

  const submit = async (ev) => {
    ev.preventDefault()
    setError('')
    if (!validate()) return
    setBusy(true)
    try {
      const u = mode === 'login' ? await login(email.trim(), password) : await register(name.trim(), email.trim(), password)
      toast({ tone: 'success', title: mode === 'login' ? `Welcome back, ${u.name.split(' ')[0]}` : 'Account created', message: u.role === 'admin' ? 'You are signed in as an administrator.' : 'You are signed in as a driver.' })
      nav(dest(u), { replace: true })
    } catch (e) {
      setError(e.message)
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-side" aria-hidden="true">
        <img src="/hero-fallback.svg" alt="" />
      </div>
      <main className="auth-main" id="main">
        <div className="auth-top">
          <Link to="/" className="brand">
            <BrandMark />
            <span>ParkSure</span>
          </Link>
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
        </div>
        <SlideUp>
          <Card className="auth-card" spotlight={false} pad>
            <h1>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
            <p className="muted" style={{ margin: '8px 0 20px' }}>
              {mode === 'login' ? 'Log in to reserve, check in and manage your bookings.' : 'Reserve parking before you arrive. The first account on a fresh install becomes the admin.'}
            </p>
            <Tabs
              label="Log in or create account"
              value={mode}
              onChange={(v) => {
                setMode(v)
                setError('')
                setFieldErr({})
              }}
              tabs={[
                { value: 'login', label: 'Log in', icon: LogIn },
                { value: 'register', label: 'Create account', icon: UserPlus },
              ]}
            />
            <form onSubmit={submit} noValidate className="stack" style={{ marginTop: 20, gap: 14 }}>
              {mode === 'register' && <Input label="Name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} error={fieldErr.name} placeholder="Alex Driver" />}
              <Input label="Email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} error={fieldErr.email} placeholder="you@example.com" />
              <Input
                label="Password"
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={fieldErr.password}
                hint={mode === 'register' ? 'At least 6 characters.' : undefined}
              />
              {error && (
                <p className="field-error" role="alert">
                  {error}
                </p>
              )}
              <Button type="submit" variant="primary" size="lg" loading={busy} icon={mode === 'login' ? LogIn : UserPlus}>
                {mode === 'login' ? 'Log in' : 'Create account'}
              </Button>
            </form>
            <div className="demo-box">
              <div className="faint">Try the seeded demo accounts</div>
              <div className="row" style={{ marginTop: 8 }}>
                {DEMOS.map((d) => (
                  <Button
                    key={d.email}
                    size="sm"
                    icon={d.icon}
                    onClick={() => {
                      setMode('login')
                      setEmail(d.email)
                      setPassword(d.password)
                      setFieldErr({})
                      setError('')
                    }}
                  >
                    {d.label}
                  </Button>
                ))}
              </div>
            </div>
          </Card>
        </SlideUp>
      </main>
    </div>
  )
}

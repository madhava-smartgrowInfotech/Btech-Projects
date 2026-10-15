import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, LogIn, Moon, Sun, UserPlus } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'
import { BrandMark, Button, Card, IconButton, Input, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'

const DEMO = { email: 'demo@biosight.app', password: 'Demo@1234' }

export default function Login() {
  const { user, login, register, expired } = useAuth()
  const { theme, toggle } = useTheme()
  const toast = useToast()
  const navigate = useNavigate()
  const loc = useLocation()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  useEffect(() => {
    document.title = `${mode === 'login' ? 'Sign in' : 'Create account'} · BioSight`
  }, [mode])

  if (user) return <Navigate to={loc.state?.from || '/app/mri'} replace />

  const go = (u) => {
    toast({ title: `Welcome, ${u.name}`, message: 'You are signed in.' })
    navigate(loc.state?.from || '/app/mri', { replace: true })
  }

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (mode === 'register' && !form.name.trim()) errs.name = 'Enter your name.'
    if (!/^\S+@\S+$/.test(form.email.trim())) errs.email = 'Enter a valid email address.'
    if (mode === 'register' ? form.password.length < 6 : !form.password) errs.password = mode === 'register' ? 'Use at least 6 characters.' : 'Enter your password.'
    setFieldErrors(errs)
    setError('')
    if (Object.keys(errs).length) return
    setBusy('form')
    try {
      go(mode === 'login' ? await login(form.email.trim(), form.password) : await register(form.name.trim(), form.email.trim(), form.password))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  const demo = async () => {
    setBusy('demo')
    setError('')
    setFieldErrors({})
    try {
      go(await login(DEMO.email, DEMO.password))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login')
    setError('')
    setFieldErrors({})
  }

  return (
    <div className="auth-wrap">
      <div style={{ position: 'fixed', top: 14, left: 16, right: 16, display: 'flex', justifyContent: 'space-between', zIndex: 2 }}>
        <Button as={Link} to="/" variant="ghost" size="sm" icon={ArrowLeft}>
          Home
        </Button>
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
      </div>
      <SlideUp className="auth-card">
        <Link to="/" className="brand" style={{ justifyContent: 'center', marginBottom: 22 }}>
          <BrandMark />
          <span>BioSight</span>
        </Link>
        <Card pad>
          <form onSubmit={submit} noValidate className="stack" style={{ gap: 16 }}>
            <div>
              <h1 style={{ fontSize: 22 }}>{mode === 'login' ? 'Sign in' : 'Create an account'}</h1>
              <p className="muted" style={{ fontSize: 14, marginTop: 6 }}>
                {mode === 'login' ? 'Open the BioSight workspace.' : 'Your analyses are saved to your own history.'}
              </p>
            </div>
            {expired && !error && (
              <p className="callout" role="status">
                Your session expired. Sign in again to continue.
              </p>
            )}
            {mode === 'register' && <Input label="Name" value={form.name} onChange={set('name')} error={fieldErrors.name} autoComplete="name" />}
            <Input label="Email" type="email" value={form.email} onChange={set('email')} error={fieldErrors.email} autoComplete="email" />
            <Input
              label="Password"
              type="password"
              value={form.password}
              onChange={set('password')}
              error={fieldErrors.password}
              hint={mode === 'register' ? 'At least 6 characters.' : undefined}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
            {error && (
              <p className="callout danger" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" variant="primary" loading={busy === 'form'} disabled={!!busy} icon={mode === 'login' ? LogIn : UserPlus}>
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
            <Button onClick={demo} loading={busy === 'demo'} disabled={!!busy}>
              Use the demo account
            </Button>
            <p className="faint" style={{ textAlign: 'center' }}>
              Demo: {DEMO.email} / {DEMO.password}
            </p>
            <Button variant="ghost" onClick={switchMode} disabled={!!busy}>
              {mode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}
            </Button>
          </form>
        </Card>
      </SlideUp>
    </div>
  )
}

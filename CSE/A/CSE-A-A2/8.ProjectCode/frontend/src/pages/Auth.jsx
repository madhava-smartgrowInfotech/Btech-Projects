import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LogIn, ShieldCheck, Siren, Timer, UserPlus } from 'lucide-react'
import { Alert, Button, Card, Checkbox, Container, Input, useToast } from '../components/ui'
import { PageTransition } from '../components/motion'
import { useAuth } from '../lib/auth'

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

function validate(mode, f) {
  const e = {}
  if (mode === 'register' && (f.name.trim().length < 2 || f.name.trim().length > 60)) e.name = 'Enter your name (2 to 60 characters).'
  if (!EMAIL_RE.test(f.email.trim())) e.email = 'Enter a valid email address.'
  if (!f.password) e.password = 'Enter your password.'
  else if (mode === 'register' && f.password.length < 8) e.password = 'Use at least 8 characters.'
  if (mode === 'register' && !e.password && f.confirm !== f.password) e.confirm = 'The passwords do not match.'
  return e
}

/** One form for both /login and /register. */
export default function Auth({ mode }) {
  const isRegister = mode === 'register'
  const { status, login, register } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const loc = useLocation()
  const from = loc.state?.from || '/monitor'
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [show, setShow] = useState(false)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (status === 'in') return <Navigate to={from} replace />

  const set = (k) => (e) => {
    setForm((f) => ({ ...f, [k]: e.target.value }))
    setErrors((er) => ({ ...er, [k]: undefined }))
    setFormError(null)
  }

  const submit = async (e) => {
    e.preventDefault()
    const er = validate(mode, form)
    setErrors(er)
    if (Object.keys(er).length) return
    setBusy(true)
    setFormError(null)
    try {
      const user = isRegister ? await register(form.name.trim(), form.email.trim(), form.password) : await login(form.email.trim(), form.password)
      toast.success(isRegister ? `Account created. Welcome, ${user.name}.` : `Signed in as ${user.name}.`)
      nav(from, { replace: true })
    } catch (err) {
      if (err.field && err.status < 500) setErrors({ [err.field]: err.message })
      else setFormError(err.status === 0 ? 'The ResQAI API is not reachable. Start it with run.bat, then try again.' : err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Container>
      <PageTransition>
        <div className="auth-grid">
          <div className="stack" style={{ '--gap': '20px' }}>
            <span className="eyebrow">{isRegister ? 'Create account' : 'Sign in'}</span>
            <h1 className="display-lg">{isRegister ? 'Join the response team' : 'Welcome back'}</h1>
            <p className="lead">
              {isRegister
                ? 'An account unlocks the live monitor, manual override and the emergency response map.'
                : 'Sign in to open the live monitor, run detections and dispatch emergency alerts.'}
            </p>
            <ul className="stack small" style={{ listStyle: 'none', padding: 0, margin: 0, '--gap': '10px' }}>
              <li className="row" style={{ '--gap': '10px' }}><Siren size={18} aria-hidden="true" /> Detect and rate crashes from sensor data</li>
              <li className="row" style={{ '--gap': '10px' }}><Timer size={18} aria-hidden="true" /> 15 second false-alarm guard before any alert</li>
              <li className="row" style={{ '--gap': '10px' }}><ShieldCheck size={18} aria-hidden="true" /> Passwords are stored as salted hashes</li>
            </ul>
          </div>

          <Card title={isRegister ? 'Create your account' : 'Sign in to ResQAI'}>
            <form onSubmit={submit} noValidate className="stack" aria-label={isRegister ? 'Create account' : 'Sign in'}>
              {formError && <Alert tone="error">{formError}</Alert>}
              {isRegister && <Input label="Name" autoComplete="name" value={form.name} onChange={set('name')} error={errors.name} data-autofocus />}
              <Input label="Email" type="email" autoComplete="email" inputMode="email" value={form.email} onChange={set('email')} error={errors.email} autoFocus={!isRegister} />
              <Input
                label="Password"
                type={show ? 'text' : 'password'}
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                value={form.password}
                onChange={set('password')}
                error={errors.password}
                hint={isRegister ? 'At least 8 characters.' : undefined}
              />
              {isRegister && <Input label="Confirm password" type={show ? 'text' : 'password'} autoComplete="new-password" value={form.confirm} onChange={set('confirm')} error={errors.confirm} />}
              <Checkbox label="Show password" checked={show} onChange={setShow} />
              <Button type="submit" variant="primary" size="lg" block loading={busy} icon={isRegister ? UserPlus : LogIn}>
                {isRegister ? 'Create account' : 'Sign in'}
              </Button>
              <p className="small muted">
                {isRegister ? 'Already have an account? ' : 'New to ResQAI? '}
                <Link to={isRegister ? '/login' : '/register'} state={loc.state} style={{ fontWeight: 700 }}>
                  {isRegister ? 'Sign in' : 'Create an account'}
                </Link>
              </p>
            </form>
          </Card>
        </div>
      </PageTransition>
    </Container>
  )
}

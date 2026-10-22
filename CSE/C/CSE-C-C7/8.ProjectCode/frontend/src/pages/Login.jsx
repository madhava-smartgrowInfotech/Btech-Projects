import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Check, LogIn } from 'lucide-react'
import { Alert, Button, Card, Container, Input } from '../components/ui'
import { useAuth } from '../lib/auth'
import { useToast } from '../components/ui'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const { user, login } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const loc = useLocation()
  const from = loc.state?.from || '/app'
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={from} replace />

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!EMAIL_RE.test(form.email.trim())) errs.email = 'Enter a valid email address.'
    if (!form.password) errs.password = 'Enter your password.'
    setErrors(errs)
    setServerError('')
    if (Object.keys(errs).length) return
    setBusy(true)
    try {
      const u = await login(form.email.trim(), form.password)
      toast.success(`Welcome back, ${u.name.split(' ')[0]}.`)
      nav(from, { replace: true })
    } catch (err) {
      setServerError(err.status === 0 ? `${err.message} Start it with run.bat, then try again.` : err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Container>
      <div className="auth-grid">
        <div className="auth-aside">
          <span className="eyebrow">Sign in</span>
          <h1 className="display-lg" style={{ marginTop: 14 }}>
            Pick up where you left off.
          </h1>
          <ul>
            <li>
              <Check aria-hidden="true" /> Your ranked courses update with every quiz, discussion and completion.
            </li>
            <li>
              <Check aria-hidden="true" /> Each recommendation shows why it was suggested.
            </li>
            <li>
              <Check aria-hidden="true" /> Your data stays in the local database.
            </li>
          </ul>
        </div>
        <Card title="Welcome back">
          <form className="stack" onSubmit={submit} noValidate style={{ '--gap': '18px' }}>
            {serverError && <Alert tone="error">{serverError}</Alert>}
            <Input label="Email" type="email" autoComplete="email" value={form.email} onChange={set('email')} error={errors.email} placeholder="you@example.com" />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={set('password')}
              error={errors.password}
            />
            <Button type="submit" variant="primary" size="lg" icon={LogIn} loading={busy} block>
              Sign in
            </Button>
            <p className="small muted">
              New here?{' '}
              <Link className="link-plain" to="/register">
                Create an account
              </Link>
            </p>
          </form>
        </Card>
      </div>
    </Container>
  )
}

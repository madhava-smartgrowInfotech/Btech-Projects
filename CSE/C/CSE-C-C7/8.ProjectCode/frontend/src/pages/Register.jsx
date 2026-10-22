import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Check, UserPlus } from 'lucide-react'
import { Alert, Button, Card, Container, Input, useToast } from '../components/ui'
import { useAuth } from '../lib/auth'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Register() {
  const { user, register } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm_password: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user && !busy) return <Navigate to="/app" replace />

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (form.name.trim().length < 2) errs.name = 'Enter your name (at least 2 characters).'
    if (!EMAIL_RE.test(form.email.trim())) errs.email = 'Enter a valid email address.'
    if (form.password.length < 6) errs.password = 'Use at least 6 characters.'
    if (form.confirm_password !== form.password) errs.confirm_password = 'Passwords do not match.'
    setErrors(errs)
    setServerError('')
    if (Object.keys(errs).length) return
    setBusy(true)
    try {
      await register({ ...form, name: form.name.trim(), email: form.email.trim() })
      toast.success('Account created. Now tell us about your learning goals.')
      nav('/app/profile', { replace: true, state: { first: true } })
    } catch (err) {
      setBusy(false)
      setServerError(err.status === 0 ? `${err.message} Start it with run.bat, then try again.` : err.message)
    }
  }

  return (
    <Container>
      <div className="auth-grid">
        <div className="auth-aside">
          <span className="eyebrow">Get started</span>
          <h1 className="display-lg" style={{ marginTop: 14 }}>
            Build your learning path.
          </h1>
          <ul>
            <li>
              <Check aria-hidden="true" /> Create an account, then a short learner profile.
            </li>
            <li>
              <Check aria-hidden="true" /> Get a ranked course list and a next best action.
            </li>
            <li>
              <Check aria-hidden="true" /> Recommendations adapt as you learn.
            </li>
          </ul>
        </div>
        <Card title="Create your account">
          <form className="stack" onSubmit={submit} noValidate style={{ '--gap': '18px' }}>
            {serverError && <Alert tone="error">{serverError}</Alert>}
            <Input label="Full name" autoComplete="name" value={form.name} onChange={set('name')} error={errors.name} />
            <Input label="Email" type="email" autoComplete="email" value={form.email} onChange={set('email')} error={errors.email} placeholder="you@example.com" />
            <Input
              label="Password"
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={set('password')}
              error={errors.password}
              hint="At least 6 characters."
            />
            <Input
              label="Confirm password"
              type="password"
              autoComplete="new-password"
              value={form.confirm_password}
              onChange={set('confirm_password')}
              error={errors.confirm_password}
            />
            <Button type="submit" variant="primary" size="lg" icon={UserPlus} loading={busy} block>
              Create account
            </Button>
            <p className="small muted">
              Already registered?{' '}
              <Link className="link-plain" to="/login">
                Sign in
              </Link>
            </p>
          </form>
        </Card>
      </div>
    </Container>
  )
}

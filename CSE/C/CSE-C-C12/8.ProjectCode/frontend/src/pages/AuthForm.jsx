import { useId, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, LogIn, UserPlus, Zap } from 'lucide-react'
import { Alert, Button, Container, Field, Input, useToast } from '../components/ui'
import { MaskHeadline } from '../components/motion'
import { DEMO_ACCOUNT, useAuth } from '../lib/auth'

export function PasswordInput({ label, error, hint, value, onChange, autoComplete, name }) {
  const id = useId()
  const [show, setShow] = useState(false)
  return (
    <Field label={label} htmlFor={id} error={error} hint={hint}>
      <div className="pw-wrap">
        <input
          id={id}
          name={name}
          className="input"
          type={show ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          aria-invalid={error ? 'true' : undefined}
          required
        />
        <button type="button" className="pw-toggle" onClick={() => setShow((s) => !s)} aria-label={show ? 'Hide password' : 'Show password'} aria-pressed={show}>
          {show ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
        </button>
      </div>
    </Field>
  )
}

/** Shared layout + submit logic for /login and /register. */
export default function AuthForm({ mode }) {
  const isLogin = mode === 'login'
  const { login, register } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const from = useLocation().state?.from || '/assistant'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [errors, setErrors] = useState({})

  const finish = (msg) => {
    toast.success(msg)
    nav(from, { replace: true })
  }

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) errs.email = 'Enter a valid email address.'
    if (!isLogin && password.length < 6) errs.password = 'Use at least 6 characters.'
    if (!isLogin && confirm !== password) errs.confirm = 'Passwords do not match.'
    setErrors(errs)
    setError('')
    if (Object.keys(errs).length) return
    setBusy(true)
    try {
      if (isLogin) await login(email.trim(), password)
      else await register(email.trim(), password)
      finish(isLogin ? 'Welcome back.' : 'Account created. You are signed in.')
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  const useDemo = async () => {
    setBusy(true)
    setError('')
    try {
      await login(DEMO_ACCOUNT.email, DEMO_ACCOUNT.password)
      finish('Signed in with the demo account.')
    } catch (err) {
      setError(`Demo sign-in failed: ${err.message}`)
      setBusy(false)
    }
  }

  return (
    <Container>
      <div className="auth-grid">
        <div className="stack" style={{ '--gap': '24px' }}>
          <span className="eyebrow">{isLogin ? 'Sign in' : 'Create account'}</span>
          <MaskHeadline
            className="display-lg"
            lines={isLogin ? ['Welcome', 'back.'] : ['Start', 'tracking.']}
          />
          <p className="lead muted">
            Private by design: accounts and consultations live in a local SQLite database on this machine. No trackers, no paid symptom APIs.
          </p>
          <div className="demo-box stack" style={{ '--gap': '10px' }}>
            <strong>Just exploring?</strong>
            <p className="small">
              Use the demo account — <code>{DEMO_ACCOUNT.email}</code> / <code>{DEMO_ACCOUNT.password}</code> — it already has sample consultations.
            </p>
            <div>
              <Button icon={Zap} onClick={useDemo} loading={busy} disabled={busy}>
                Continue with demo account
              </Button>
            </div>
          </div>
        </div>

        <form className="card stack" onSubmit={submit} noValidate aria-label={isLogin ? 'Sign in' : 'Create account'} style={{ '--gap': '18px' }}>
          <h2 className="display-md">{isLogin ? 'Sign in' : 'Create account'}</h2>
          {error && <Alert tone="error">{error}</Alert>}
          <Input
            label="Email"
            type="email"
            name="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            required
          />
          <PasswordInput
            label="Password"
            name="password"
            value={password}
            onChange={setPassword}
            error={errors.password}
            hint={isLogin ? undefined : 'At least 6 characters.'}
            autoComplete={isLogin ? 'current-password' : 'new-password'}
          />
          {!isLogin && <PasswordInput label="Confirm password" name="confirm" value={confirm} onChange={setConfirm} error={errors.confirm} autoComplete="new-password" />}
          <Button type="submit" variant="primary" size="lg" block loading={busy} icon={isLogin ? LogIn : UserPlus}>
            {isLogin ? 'Sign in' : 'Create account'}
          </Button>
          <p className="small muted" style={{ textAlign: 'center' }}>
            {isLogin ? (
              <>
                No account? <Link to="/register" state={{ from }} style={{ fontWeight: 700 }}>Create one</Link>
              </>
            ) : (
              <>
                Already registered? <Link to="/login" state={{ from }} style={{ fontWeight: 700 }}>Sign in</Link>
              </>
            )}
          </p>
        </form>
      </div>
    </Container>
  )
}

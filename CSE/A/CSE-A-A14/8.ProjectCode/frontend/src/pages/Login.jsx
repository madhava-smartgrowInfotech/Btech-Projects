import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, KeyRound, Lock, ShieldCheck, Sparkles, Wand2 } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { Brand, Button, Card, Input, useToast } from '../components/ui'
import { Callout } from '../components/app'
import { SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'

const DEMO = { email: 'demo@churniq.com', password: 'Demo@1234' }

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [errors, setErrors] = useState({})
  const dest = loc.state?.from || '/app'

  if (user) return <Navigate to={dest} replace />

  const submit = async (e, creds) => {
    e?.preventDefault()
    const em = (creds?.email ?? email).trim()
    const pw = creds?.password ?? password
    const next = {}
    if (!em) next.email = 'Enter your email address.'
    else if (!/^\S+@\S+\.\S+$/.test(em)) next.email = 'That does not look like an email address.'
    if (!pw) next.password = 'Enter your password.'
    setErrors(next)
    setError('')
    if (Object.keys(next).length) return
    setBusy(true)
    try {
      await login(em, pw)
      toast({ kind: 'success', title: 'Welcome back', message: 'Signed in as the demo analyst.' })
      nav(dest, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const useDemo = () => {
    setEmail(DEMO.email)
    setPassword(DEMO.password)
    setErrors({})
    setError('')
  }

  return (
    <div className="auth">
      <main className="auth-form" id="main">
        <Brand />
        <SlideUp>
          <h1>Sign in to ChurnIQ</h1>
          <p className="muted" style={{ marginTop: 8 }}>
            Explainable churn prediction and retention intelligence for telecom teams.
          </p>
        </SlideUp>

        <div className="demo-box" aria-label="Demo account">
          <div className="row between">
            <strong style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
              <KeyRound size={17} aria-hidden="true" /> Demo account
            </strong>
            <Button size="sm" variant="secondary" icon={Wand2} onClick={useDemo}>
              Fill credentials
            </Button>
          </div>
          <dl>
            <dt>Email</dt>
            <dd className="mono">{DEMO.email}</dd>
            <dt>Password</dt>
            <dd className="mono">{DEMO.password}</dd>
          </dl>
        </div>

        <form onSubmit={submit} noValidate className="stack" style={{ '--gap': '16px' }}>
          {error && (
            <Callout tone="error" title="Could not sign in">
              {error}
            </Callout>
          )}
          <Input id="email" type="email" label="Email" autoComplete="username" placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} />
          <div className="field">
            <label className="field-label" htmlFor="password">
              Password
            </label>
            <div className="pw-wrap">
              <input
                id="password"
                className="input"
                type={show ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={errors.password ? 'true' : undefined}
                aria-describedby={errors.password ? 'password-err' : undefined}
              />
              <button type="button" className="icon-btn" aria-label={show ? 'Hide password' : 'Show password'} aria-pressed={show} onClick={() => setShow((s) => !s)}>
                {show ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
              </button>
            </div>
            {errors.password && (
              <span className="field-error" id="password-err" role="alert">
                {errors.password}
              </span>
            )}
          </div>
          <Button type="submit" size="lg" block loading={busy} iconRight={ArrowRight}>
            Sign in
          </Button>
          <Button variant="ghost" block onClick={(e) => submit(e, DEMO)} disabled={busy} icon={Sparkles}>
            One-click demo sign in
          </Button>
        </form>

        <p className="small muted">
          <Link to="/" className="link-cell">
            ← Back to the landing page
          </Link>
        </p>
      </main>

      <aside className="auth-side" aria-hidden="true">
        <Blobs preset="auth" />
        <Stagger className="quote-card">
          <Stagger.Item>
            <Card tint="mint" hover={false}>
              <ShieldCheck size={26} aria-hidden="true" />
              <h3 style={{ marginTop: 10 }}>Runs entirely on your machine</h3>
              <p className="small muted" style={{ marginTop: 6 }}>
                No customer data leaves this computer, and no external AI service is called. Models, explanations and recommendations are all local Python.
              </p>
            </Card>
          </Stagger.Item>
          <Stagger.Item>
            <Card hover={false}>
              <Lock size={24} aria-hidden="true" />
              <h3 style={{ marginTop: 10 }}>Why, not just who</h3>
              <p className="small muted" style={{ marginTop: 6 }}>
                Every score comes with the factors behind it and a suggested retention action, never a bare number.
              </p>
            </Card>
          </Stagger.Item>
        </Stagger>
      </aside>
    </div>
  )
}

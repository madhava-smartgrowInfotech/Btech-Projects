import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, KeyRound, Network, ShieldCheck, Sparkles, UserCog } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { Brand, Button, Card, Input, useToast } from '../components/ui'
import { Callout } from '../components/app'
import { SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'

const PASSWORD = 'Demo@1234'
const DEMOS = [
  { role: 'moderator', email: 'moderator@botgraph.app', icon: ShieldCheck, text: 'Can review the queue, confirm or dismiss, and retrain.' },
  { role: 'analyst', email: 'analyst@botgraph.app', icon: UserCog, text: 'Read-only: explore accounts, botnets and model results.' },
]

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
      const u = await login(em, pw)
      toast({ kind: 'success', title: `Signed in as ${u.role}`, message: `Welcome, ${u.name}.` })
      nav(dest, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const fill = (d) => {
    setEmail(d.email)
    setPassword(PASSWORD)
    setErrors({})
    setError('')
  }

  return (
    <div className="auth">
      <main className="auth-form" id="main">
        <Brand />
        <SlideUp>
          <h1>Sign in to BotGraph</h1>
          <p className="muted" style={{ marginTop: 8 }}>
            Find fake accounts and coordinated botnets from the shape of the social graph.
          </p>
        </SlideUp>

        <div className="demo-box" aria-label="Demo accounts">
          <strong style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
            <KeyRound size={17} aria-hidden="true" /> Demo accounts
          </strong>
          <dl>
            <dt>Password</dt>
            <dd className="mono">{PASSWORD}</dd>
          </dl>
          <div className="stack" style={{ '--gap': '10px' }}>
            {DEMOS.map((d) => (
              <div key={d.role} className="row between" style={{ '--gap': '10px' }}>
                <span style={{ minWidth: 0 }}>
                  <b style={{ textTransform: 'capitalize' }}>{d.role}</b> <span className="mono">{d.email}</span>
                  <span className="tiny muted" style={{ display: 'block' }}>
                    {d.text}
                  </span>
                </span>
                <Button size="sm" variant="secondary" icon={d.icon} onClick={() => fill(d)}>
                  Fill
                </Button>
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={submit} noValidate className="stack" style={{ '--gap': '16px' }}>
          {error && (
            <Callout tone="error" title="Could not sign in">
              {error}
            </Callout>
          )}
          <Input id="email" type="email" label="Email" autoComplete="username" placeholder="you@botgraph.app" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} />
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
          <Button variant="ghost" block onClick={(e) => submit(e, { email: DEMOS[0].email, password: PASSWORD })} disabled={busy} icon={Sparkles}>
            One-click demo sign in (moderator)
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
              <Network size={26} aria-hidden="true" />
              <h3 style={{ marginTop: 10 }}>Accounts are judged by their company</h3>
              <p className="small muted" style={{ marginTop: 6 }}>
                A profile can look ordinary on its own. The accounts it follows, likes and moves with tell the rest of the story.
              </p>
            </Card>
          </Stagger.Item>
          <Stagger.Item>
            <Card hover={false}>
              <ShieldCheck size={24} aria-hidden="true" />
              <h3 style={{ marginTop: 10 }}>You make the call</h3>
              <p className="small muted" style={{ marginTop: 6 }}>
                Every flag shows its reasons. Moderator decisions are logged and feed the next training run.
              </p>
            </Card>
          </Stagger.Item>
        </Stagger>
      </aside>
    </div>
  )
}

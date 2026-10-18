import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, Eye, EyeOff, KeyRound, LogIn, ShieldCheck } from 'lucide-react'
import { DEMO_ACCOUNT, useAuth } from '../lib/auth'
import { BrandMark } from '../components/ui/layout'
import { Button, Checkbox, IconButton, Input } from '../components/ui/controls'
import { Card } from '../components/ui/display'
import { useTheme } from '../lib/theme'
import { Moon, Sun } from 'lucide-react'
import { FadeIn, SlideUp } from '../components/motion'

export default function Login() {
  const { user, login } = useAuth()
  const { theme, toggle } = useTheme()
  const nav = useNavigate()
  const loc = useLocation()
  const dest = loc.state?.from && loc.state.from.startsWith('/app') ? loc.state.from : '/app'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    document.title = 'Sign in · SafeGrid-AI'
  }, [])

  if (user) return <Navigate to={dest} replace />

  const submit = (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    const r = login(email, password)
    if (r.ok) nav(dest, { replace: true })
    else {
      setError(r.error)
      setBusy(false)
    }
  }

  const useDemo = () => {
    setEmail(DEMO_ACCOUNT.email)
    setPassword(DEMO_ACCOUNT.password)
    setError(null)
    login(DEMO_ACCOUNT.email, DEMO_ACCOUNT.password)
    nav(dest, { replace: true })
  }

  return (
    <div className="auth-page">
      <div className="auth-side">
        <Link to="/" className="brand">
          <BrandMark />
          <span>SafeGrid-AI<small>Shielded multi-agent grid control</small></span>
        </Link>
        <SlideUp>
          <h1>Let the agents propose.<br /><span className="text-grad">Let the shield decide.</span></h1>
          <p className="muted">
            Sign in to the operator console to run scenarios, watch three AI agents negotiate a small low-voltage feeder, and see every proposal checked by the Symbolic Safety Shield before it touches the grid.
          </p>
        </SlideUp>
        <ul className="auth-points">
          <li><ShieldCheck size={18} aria-hidden="true" /> Only validated actions are ever executed</li>
          <li><KeyRound size={18} aria-hidden="true" /> Every intervention is written to a hash-chained audit log</li>
        </ul>
      </div>

      <main className="auth-main" id="main">
        <div className="auth-top">
          <Link to="/" className="btn btn-ghost btn-sm"><ArrowLeft size={15} aria-hidden="true" /> Back to site</Link>
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
        </div>
        <FadeIn>
          <Card className="auth-card" spotlight={false}>
            <div className="auth-card-in">
              <h2>Sign in</h2>
              <p className="muted">Use the demo operator account to explore the console.</p>
              <form onSubmit={submit} noValidate className="stack" style={{ marginTop: 22 }}>
                <Input label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={DEMO_ACCOUNT.email} required />
                <div className="pw-field">
                  <Input label="Password" type={show ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                  <IconButton className="pw-toggle" icon={show ? EyeOff : Eye} label={show ? 'Hide password' : 'Show password'} size="sm" onClick={() => setShow((s) => !s)} />
                </div>
                {error && <div className="notice danger" role="alert">{error}</div>}
                <Button type="submit" variant="primary" icon={LogIn} loading={busy} disabled={!email || !password}>Sign in</Button>
              </form>
              <div className="auth-divider"><span>or</span></div>
              <Button onClick={useDemo} className="auth-demo" icon={KeyRound}>Continue with the demo account</Button>
              <div className="demo-box">
                <div className="faint">Demo credentials</div>
                <div className="mono">{DEMO_ACCOUNT.email}</div>
                <div className="mono">{DEMO_ACCOUNT.password}</div>
                <p className="faint">The demo sign-in only gates this browser session; the SafeGrid-AI API itself has no user accounts.</p>
              </div>
            </div>
          </Card>
        </FadeIn>
      </main>
    </div>
  )
}

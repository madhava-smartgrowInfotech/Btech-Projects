import { useEffect, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { AlertTriangle, KeyRound, LogIn } from 'lucide-react'
import { DEMO_USER, useAuth } from '../lib/auth'
import { Brand, Button, Checkbox, Input, ThemeToggle, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const loc = useLocation()
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [errors, setErrors] = useState({})
  const [failed, setFailed] = useState(false)
  const [busy, setBusy] = useState(false)
  const from = loc.state?.from || '/app'

  useEffect(() => {
    document.title = 'Sign in · FinSight AI'
  }, [])

  if (user) return <Navigate to={from} replace />

  const submit = (e) => {
    e.preventDefault()
    const errs = {}
    if (!email.trim()) errs.email = 'Enter your email.'
    else if (!/^\S+@\S+\.\S+$/.test(email.trim())) errs.email = 'Enter a valid email address.'
    if (!password) errs.password = 'Enter your password.'
    setErrors(errs)
    setFailed(false)
    if (Object.keys(errs).length) return
    setBusy(true)
    // short pause so the loading state is visible; the check itself is local
    setTimeout(() => {
      if (login(email, password)) {
        toast({ kind: 'success', title: `Welcome, ${DEMO_USER.name}`, message: 'You are signed in with the sample account.' })
        navigate(from, { replace: true })
      } else {
        setFailed(true)
        setBusy(false)
      }
    }, 450)
  }

  const fillDemo = () => {
    setEmail(DEMO_USER.email)
    setPassword(DEMO_USER.password)
    setErrors({})
    setFailed(false)
  }

  return (
    <main id="main" className="login-wrap">
      <Blobs preset="hero" />
      <div className="row" style={{ position: 'absolute', top: 16, left: 16, right: 16, justifyContent: 'space-between', zIndex: 2 }}>
        <Brand />
        <ThemeToggle />
      </div>
      <SlideUp className="login-card">
        <form onSubmit={submit} noValidate className="stack" style={{ '--gap': '16px' }}>
          <div>
            <span className="eyebrow"><KeyRound size={14} aria-hidden="true" />Sample login</span>
            <h1 style={{ marginTop: 12, fontSize: 'clamp(26px, 6vw, 32px)' }}>Welcome back</h1>
            <p className="muted" style={{ marginTop: 6 }}>Sign in to open your FinSight AI workspace.</p>
          </div>

          <div className="login-demo">
            <strong>Demo account</strong>
            <p style={{ marginTop: 4 }}>Email <code>{DEMO_USER.email}</code></p>
            <p style={{ marginTop: 4 }}>Password <code>{DEMO_USER.password}</code></p>
            <Button variant="secondary" size="sm" onClick={fillDemo} style={{ marginTop: 10 }}>Use demo credentials</Button>
          </div>

          {failed && (
            <div className="state error" role="alert" style={{ alignItems: 'flex-start', textAlign: 'left', padding: '14px 16px' }}>
              <strong className="row" style={{ '--gap': '8px' }}><AlertTriangle size={18} aria-hidden="true" />Email or password is incorrect</strong>
              <p className="small">Use the demo account above, or press “Use demo credentials”.</p>
            </div>
          )}

          <Input id="login-email" label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} required />
          <Input id="login-password" label="Password" type={show ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} required />
          <Checkbox label="Show password" checked={show} onChange={setShow} />

          <Button type="submit" size="lg" block icon={LogIn} loading={busy}>Sign in</Button>
          <p className="small muted">Sample login for demonstration only: it runs in your browser and protects nothing. FinSight AI has no user accounts or stored personal data.</p>
        </form>
      </SlideUp>
    </main>
  )
}

import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, LogIn, Wand2 } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { useConfig } from '../lib/config'
import { BrandMark, Button, Card, Input } from '../components/ui'
import { SlideUp } from '../components/motion'
import { Callout } from '../components/lab'
import '../styles/landing.css'

export default function Login() {
  const { user, login } = useAuth()
  const { config } = useConfig()
  const navigate = useNavigate()
  const loc = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const dest = loc.state?.from || '/app'

  useEffect(() => {
    document.title = 'Sign in · LabLens'
  }, [])

  if (user) return <Navigate to={dest} replace />

  const submit = async (e, creds) => {
    e?.preventDefault()
    const em = creds?.email ?? email
    const pw = creds?.password ?? password
    if (!em.trim() || !pw) {
      setError('Enter both your email and password.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await login(em.trim(), pw)
      navigate(dest, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const useDemo = () => {
    if (!config) return
    setEmail(config.demo_email)
    setPassword(config.demo_password)
    submit(null, { email: config.demo_email, password: config.demo_password })
  }

  return (
    <div className="auth-wrap landing">
      <span className="orb orb-a" aria-hidden="true" />
      <span className="orb orb-b" aria-hidden="true" />
      <SlideUp>
        <Card className="auth-card">
          <Link to="/" className="brand" style={{ padding: 0 }}>
            <BrandMark />
            <span>LabLens</span>
          </Link>
          <h1>Sign in</h1>
          <p className="muted" style={{ margin: 0 }}>
            Open your lab report workspace.
          </p>
          <form onSubmit={submit} noValidate>
            {error && (
              <Callout tone="danger" icon={LogIn}>
                {error}
              </Callout>
            )}
            <Input label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" data-autofocus />
            <Input label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button type="submit" variant="primary" size="lg" loading={busy} icon={LogIn}>
              Sign in
            </Button>
          </form>
          <div className="demo-box">
            <strong style={{ color: 'var(--text)' }}>Demo account</strong>
            <div style={{ margin: '6px 0 12px' }}>
              {config ? (
                <>
                  <code>{config.demo_email}</code> · <code>{config.demo_password}</code>
                </>
              ) : (
                'Loading…'
              )}
            </div>
            <Button size="sm" icon={Wand2} onClick={useDemo} disabled={!config || busy}>
              Sign in as demo user
            </Button>
          </div>
          <Button as={Link} to="/" variant="ghost" size="sm" icon={ArrowLeft} style={{ marginTop: 14 }}>
            Back to landing page
          </Button>
        </Card>
      </SlideUp>
    </div>
  )
}

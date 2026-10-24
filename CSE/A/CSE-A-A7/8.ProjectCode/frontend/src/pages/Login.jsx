import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LogIn, ShieldCheck } from 'lucide-react'
import { Alert, Button, Card, Container, Input } from '../components/ui'
import { MaskHeadline, SlideUp } from '../components/motion'
import { useAuth } from '../lib/auth'
import { useToast } from '../components/ui'

const DEMOS = [
  { role: 'Clinician', email: 'clinician@athena.health', password: 'Athena@123' },
  { role: 'Admin', email: 'admin@athena.health', password: 'Athena@123' },
]

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  if (user) return <Navigate to={loc.state?.from || '/app/queue'} replace />

  const submit = async (e, creds) => {
    e?.preventDefault()
    const em = (creds?.email ?? email).trim()
    const pw = creds?.password ?? password
    if (!em || !pw) {
      setError('Enter your email and password.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const u = await login(em, pw)
      toast.success(`Signed in as ${u.name}.`)
      nav(loc.state?.from || '/app/queue', { replace: true })
    } catch (err) {
      setError(err.status === 0 ? 'Cannot reach the ATHENA API. Start it with run.bat, then try again.' : err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Container>
      <div className="auth-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 340px), 1fr))' }}>
        <div className="stack" style={{ '--gap': '20px' }}>
          <span className="eyebrow">Staff sign-in</span>
          <MaskHeadline className="display-lg" lines={['Back on', 'the floor.']} />
          <p className="lead" style={{ maxWidth: '40ch' }}>
            Sign in to triage new arrivals, review the queue and override a priority with a reason.
          </p>
        </div>
        <SlideUp>
          <Card title="Sign in" tone="lime" hot>
            <form className="stack" onSubmit={submit} noValidate>
              {error && <Alert tone="error">{error}</Alert>}
              <Input label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
              <Input label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <Button variant="primary" type="submit" icon={LogIn} loading={busy} block>
                Sign in
              </Button>
            </form>
          </Card>
          <div className="demo-box stack" style={{ marginTop: 20, '--gap': '10px' }}>
            <span className="dot-row">
              <ShieldCheck size={14} aria-hidden="true" /> Demo accounts
            </span>
            <p className="small">One click signs in. Both use the password Athena@123.</p>
            <div className="row">
              {DEMOS.map((d) => (
                <Button key={d.role} size="sm" disabled={busy} onClick={() => submit(null, d)}>
                  {d.role}
                </Button>
              ))}
            </div>
          </div>
        </SlideUp>
      </div>
    </Container>
  )
}

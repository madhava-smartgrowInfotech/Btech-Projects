import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { KeyRound, LogIn } from 'lucide-react'
import { Alert, Button, Card, Checkbox, Container, Input } from '../components/ui'
import { useToast } from '../components/ui'
import { MaskHeadline } from '../components/motion'
import { useAuth } from '../lib/auth'
import { useDocumentTitle } from '../lib/hooks'

const DEMO = { email: 'demo@pneumodetect.ai', password: 'Pneumo@123' }

export default function Login() {
  useDocumentTitle('Sign in')
  const { user, login } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const loc = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [touched, setTouched] = useState(false)

  const dest = loc.state?.from || '/app'
  if (user) return <Navigate to={dest} replace />

  const submit = async (e) => {
    e.preventDefault()
    setTouched(true)
    if (!email.trim() || !password) return
    setBusy(true)
    setError('')
    try {
      const u = await login(email, password)
      toast.success(`Signed in as ${u.name}.`)
      nav(dest, { replace: true })
    } catch (err) {
      setError(err.status === 0 ? 'The API server is not reachable. Start it with run.bat, then try again.' : err.message)
      setBusy(false)
    }
  }

  return (
    <Container>
      <div className="auth-grid">
        <div className="stack" style={{ '--gap': '20px' }}>
          <span className="eyebrow">Demo access</span>
          <MaskHeadline className="display-lg" lines={['Sign in', 'to scan.']} />
          <p className="lead">The scans, heatmaps and history live behind a login. Use the demo account below to try the full workflow.</p>
          <div className="cred-box">
            <span className="tiny mono muted">DEMO ACCOUNT</span>
            <div>
              Email: <code>{DEMO.email}</code>
            </div>
            <div>
              Password: <code>{DEMO.password}</code>
            </div>
          </div>
        </div>

        <Card title="Sign in">
          <form onSubmit={submit} noValidate className="stack">
            {error && <Alert tone="error">{error}</Alert>}
            <Input
              label="Email"
              type="email"
              name="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={touched && !email.trim() ? 'Enter your email.' : undefined}
              required
            />
            <Input
              label="Password"
              type={show ? 'text' : 'password'}
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={touched && !password ? 'Enter your password.' : undefined}
              required
            />
            <Checkbox label="Show password" checked={show} onChange={setShow} />
            <Button type="submit" variant="primary" icon={LogIn} loading={busy} block>
              Sign in
            </Button>
            <Button
              icon={KeyRound}
              block
              disabled={busy}
              onClick={() => {
                setEmail(DEMO.email)
                setPassword(DEMO.password)
                setError('')
              }}
            >
              Fill demo credentials
            </Button>
          </form>
        </Card>
      </div>
    </Container>
  )
}

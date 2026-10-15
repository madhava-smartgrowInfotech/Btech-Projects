import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LogIn } from 'lucide-react'
import { PublicShell, Container } from '../components/ui/Layout.jsx'
import { Alert, Button, Card, Input } from '../components/ui/index.js'
import { useToast } from '../components/ui/Toast.jsx'
import { MaskHeadline } from '../components/motion/index.jsx'
import { useAuth } from '../lib/auth.jsx'
import { errorMessage } from '../api.js'

const DEMO = [
  { label: 'Doctor', email: 'doctor@pulmovision.app', password: 'Doctor@123', note: 'Reviews results, reports and the audit log' },
  { label: 'Technician', email: 'tech@pulmovision.app', password: 'Tech@123', note: 'Registers patients and uploads scans' },
]

export default function Login() {
  const { user, login } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const loc = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  if (user) return <Navigate to="/scan" replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const signedIn = await login(email.trim(), password)
      toast.success(`Signed in as ${signedIn.name}.`)
      nav(loc.state?.from || '/scan', { replace: true })
    } catch (err) {
      setError(await errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <PublicShell>
      <Container>
        <div className="auth-grid">
          <section className="stack" style={{ '--gap': '20px' }}>
            <span className="eyebrow">Secure sign-in</span>
            <MaskHeadline as="h1" className="display-lg" lines={['Sign in to', 'the workspace.']} />
            <p className="lead muted">
              Access is role-based. Doctors review AI results, reports and the audit log; technicians register patients and upload scans.
            </p>
            <Card title="Demo accounts">
              <div className="page" style={{ gap: 12 }}>
                {DEMO.map((d) => (
                  <div key={d.email} className="stack" style={{ '--gap': '6px' }}>
                    <span className="small"><strong>{d.label}</strong> · {d.note}</span>
                    <span className="tiny mono">{d.email} / {d.password}</span>
                    <div>
                      <Button size="sm" onClick={() => { setEmail(d.email); setPassword(d.password); setError('') }}>
                        Fill {d.label.toLowerCase()} login
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </section>

          <Card as="form" onSubmit={submit} title="Sign in">
            <div className="page" style={{ gap: 16 }}>
              <Input id="login-email" label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
              <Input id="login-password" label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              {error && <Alert tone="error">{error}</Alert>}
              <Button type="submit" variant="primary" size="lg" icon={LogIn} loading={busy} block>
                {busy ? 'Signing in…' : 'Sign in'}
              </Button>
            </div>
          </Card>
        </div>
      </Container>
    </PublicShell>
  )
}

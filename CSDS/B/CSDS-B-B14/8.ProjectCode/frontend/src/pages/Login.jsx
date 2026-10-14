import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, LogIn } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { errorText } from '../api'
import { Brand, Button, Card, Input, useToast } from '../components/ui'

const DEMO = [
  { role: 'Engineer', email: 'engineer@aquavision.local', password: 'engineer123', note: 'Can inject and repair leaks on the twin' },
  { role: 'Manager', email: 'manager@aquavision.local', password: 'manager123', note: 'Views everything and runs what-if plans' },
]

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const toast = useToast()
  const [email, setEmail] = useState(DEMO[0].email)
  const [password, setPassword] = useState(DEMO[0].password)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  if (user) return <Navigate to="/dashboard" replace />

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const u = await login(email.trim(), password)
      toast({ kind: 'success', title: `Signed in as ${u.name}`, message: `${u.role} account` })
      nav(loc.state?.from || '/dashboard', { replace: true })
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '40px 16px' }}>
      <div className="stack" style={{ width: 'min(440px, 100%)', '--gap': '20px' }}>
        <div className="row between">
          <Brand />
          <Button variant="ghost" size="sm" icon={ArrowLeft} to="/">
            Home
          </Button>
        </div>
        <Card as="form" hover={false} onSubmit={submit} noValidate title="Sign in" subtitle="Use a demo account, or your utility login.">
          <div className="stack" style={{ '--gap': '16px' }}>
            <Input id="email" label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input
              id="password"
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && (
              <p className="field-error" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" block size="lg" icon={LogIn} loading={busy}>
              Sign in
            </Button>
          </div>
          <div style={{ marginTop: 22, paddingTop: 18, borderTop: '1px solid var(--border)' }}>
            <p className="small muted" style={{ marginBottom: 10 }}>
              Demo accounts
            </p>
            <div className="stack" style={{ '--gap': '10px' }}>
              {DEMO.map((d) => (
                <Button
                  key={d.role}
                  variant="secondary"
                  block
                  style={{ height: 'auto', minHeight: 56, padding: '12px 16px', justifyContent: 'flex-start', textAlign: 'left' }}
                  aria-label={`Fill in the ${d.role} demo account`}
                  onClick={() => {
                    setEmail(d.email)
                    setPassword(d.password)
                    setError('')
                  }}
                >
                  <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <strong>{d.role}</strong>
                    <span className="tiny muted">{d.note}</span>
                  </span>
                </Button>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

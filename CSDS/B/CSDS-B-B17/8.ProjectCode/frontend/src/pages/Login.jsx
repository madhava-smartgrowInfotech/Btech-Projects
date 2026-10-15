import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LogIn } from 'lucide-react'
import { errorText } from '../api'
import { useAuth } from '../lib/auth'
import { Alert, Button, Card, Container, Input, useToast } from '../components/ui'
import { MaskHeadline } from '../components/motion'

const DEMO = [
  { email: 'supervisor@callsense.local', name: 'Supervisor', note: 'sees every call and the whole team' },
  { email: 'agent@callsense.local', name: 'Agent (Alex)', note: 'sees only their own calls' },
]

export default function Login() {
  const nav = useNavigate()
  const loc = useLocation()
  const toast = useToast()
  const { user, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (user) return <Navigate to={loc.state?.from || '/calls'} replace />

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const u = await login(email.trim(), password)
      toast.success(`Signed in as ${u.name}.`)
      nav('/calls')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container>
      <div className="auth-grid">
        <div className="stack" style={{ '--gap': '20px' }}>
          <span className="eyebrow">Sign in</span>
          <MaskHeadline as="h1" className="display-lg" lines={['Back to', 'the calls.']} />
          <p className="lead muted">Supervisors see the whole team. Agents see only the calls they handled.</p>
          <Card title="Demo accounts" flat>
            <p className="small muted" style={{ marginBottom: 12 }}>
              Pick one to fill the email, then enter the demo password from the README.
            </p>
            <div className="stack" style={{ '--gap': '10px' }}>
              {DEMO.map((d) => (
                <Button key={d.email} onClick={() => setEmail(d.email)} block aria-label={`Use ${d.name} demo account`}>
                  {d.name}
                  <span className="tiny" style={{ opacity: 0.7, fontWeight: 500 }}>
                    {d.note}
                  </span>
                </Button>
              ))}
            </div>
          </Card>
        </div>
        <Card title="Sign in" className="login-card">
          <form onSubmit={submit} className="stack" noValidate>
            <Input label="Email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
            <Input label="Password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            {error && <Alert tone="error">{error}</Alert>}
            <Button type="submit" variant="primary" size="lg" icon={LogIn} loading={loading} disabled={!email || !password}>
              Sign in
            </Button>
          </form>
        </Card>
      </div>
    </Container>
  )
}

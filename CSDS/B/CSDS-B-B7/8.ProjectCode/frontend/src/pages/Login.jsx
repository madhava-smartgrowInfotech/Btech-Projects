import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn, ShieldCheck } from 'lucide-react'
import api, { errorMessage } from '../api'
import { useAuth } from '../lib/auth'
import { PublicShell } from '../components/ui/Layout'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Form'
import { Alert } from '../components/ui/Feedback'
import { useToast } from '../components/ui/Toast'
import { FadeIn, MaskHeadline, SlideUp } from '../components/motion'

const DEMO = [
  { role: 'Administrator', email: 'admin@hospisense.app', password: 'Admin@123' },
  { role: 'Doctor', email: 'doctor@hospisense.app', password: 'Doctor@123' },
]

export default function Login() {
  const { login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/auth/login', { email, password })
      login(data)
      toast.success(`Signed in as ${data.user.name}.`)
      navigate('/dashboard')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <PublicShell>
      <section className="auth-grid container">
        <div>
          <FadeIn>
            <span className="eyebrow">Staff sign-in</span>
          </FadeIn>
          <MaskHeadline as="h1" className="display-xl" lines={['Sign in to', 'HospiSense']} />
          <SlideUp delay={0.2}>
            <p className="lead" style={{ marginTop: 24 }}>
              Administrators run and accept allocation plans. Doctors and bed managers can predict stays and review every forecast.
            </p>
          </SlideUp>
        </div>

        <SlideUp delay={0.15}>
          <form className="card" onSubmit={submit} noValidate={false} aria-describedby={error ? 'login-error' : undefined}>
            <h2 className="card-title" style={{ marginBottom: 18 }}>
              Account
            </h2>
            {error && (
              <div id="login-error" style={{ marginBottom: 16 }}>
                <Alert tone="error">{error}</Alert>
              </div>
            )}
            <div className="stack" style={{ '--gap': '16px' }}>
              <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
              <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
              <Button type="submit" variant="primary" size="lg" block loading={loading} icon={LogIn}>
                {loading ? 'Signing in' : 'Sign in'}
              </Button>
            </div>
          </form>

          <div className="card card-flat" style={{ marginTop: 20 }}>
            <h3 className="display-sm" style={{ fontSize: '1.3rem' }}>
              Demo accounts
            </h3>
            <p className="small muted" style={{ margin: '8px 0 14px' }}>
              Fill the form with a demo account, then sign in.
            </p>
            <div className="row">
              {DEMO.map((d) => (
                <Button
                  key={d.email}
                  size="sm"
                  onClick={() => {
                    setEmail(d.email)
                    setPassword(d.password)
                    setError('')
                  }}
                >
                  {d.role}
                </Button>
              ))}
            </div>
          </div>

          <p className="small muted" style={{ marginTop: 20, display: 'flex', gap: 8 }}>
            <ShieldCheck size={16} aria-hidden="true" style={{ flex: 'none', marginTop: 2 }} />
            Decision support only. Predictions support, and do not replace, clinical judgement.
          </p>
        </SlideUp>
      </section>
    </PublicShell>
  )
}

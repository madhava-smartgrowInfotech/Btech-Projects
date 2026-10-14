import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useAuth } from '../auth'
import { errMsg } from '../api'
import { BrandMark, Button, Card, Input, Tabs, useToast } from '../components/ui'
import { FadeIn } from '../components/motion'

const MODES = [
  { value: 'login', label: 'Sign in' },
  { value: 'register', label: 'Register' },
]

export default function Login() {
  const { email: signedIn, login } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('demo@apisentry.local')
  const [password, setPassword] = useState('demo12345')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (signedIn) return <Navigate to="/app/targets" replace />

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!email.includes('@')) return setError('Enter an email address.')
    if (mode === 'register' && password.length < 6) return setError('Use at least 6 characters for the password.')
    setBusy(true)
    try {
      await login(email.trim(), password, mode === 'register')
      toast({ title: mode === 'register' ? 'Account created' : 'Signed in', message: email.trim() })
      navigate('/app/targets')
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <FadeIn className="auth-card">
        <div className="auth-brand">
          <BrandMark size={22} />
          APISentry
        </div>
        <Card pad spotlight={false}>
          <Tabs label="Sign in or register" tabs={MODES} value={mode} onChange={(m) => { setMode(m); setError('') }} />
          <form onSubmit={submit} noValidate className="form-stack" style={{ marginTop: 20 }}>
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              hint={mode === 'register' ? 'At least 6 characters.' : undefined}
              required
            />
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" variant="primary" size="lg" loading={busy} iconRight={ArrowRight}>
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>
          <p className="faint" style={{ marginTop: 18, textAlign: 'center' }}>
            Demo login is pre-filled: <strong>demo@apisentry.local</strong> / <strong>demo12345</strong>
          </p>
        </Card>
      </FadeIn>
    </main>
  )
}

import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, GraduationCap, LogIn, ShieldCheck, UserPlus, Users } from 'lucide-react'
import { Button, Card, Input, Select, Tabs, useToast, Badge } from '../components/ui'
import { BrandMark, homeFor } from '../components/ui/layout'
import { SlideUp } from '../components/motion'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'

const DEMO_PASSWORD = 'Demo@1234'
const DEMOS = [
  { role: 'Student', email: 'student@example.com', icon: GraduationCap, text: 'Learning, graph, marketplace, interviews, coding' },
  { role: 'Mentor', email: 'mentor@example.com', icon: Users, text: 'Accept requests, give feedback, sell resources' },
  { role: 'Admin', email: 'admin@example.com', icon: ShieldCheck, text: 'Verify mentors, moderate users and resources' },
]

function SignIn({ onDone }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      onDone(await login(email, password))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="stack" style={{ gap: 16 }} noValidate>
      <Input label="Email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <Input
        label="Password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        error={error || undefined}
      />
      <Button type="submit" variant="primary" size="lg" icon={LogIn} loading={busy} disabled={!email || !password}>
        Sign in
      </Button>
    </form>
  )
}

function Register({ onCreated }) {
  const toast = useToast()
  const [f, setF] = useState({ name: '', email: '', password: '', role: 'student' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const r = await api.post('/auth/register', f)
      toast({ title: 'Account created', message: r.message, duration: 8000 })
      onCreated(f.email)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="stack" style={{ gap: 16 }} noValidate>
      <Input label="Full name" autoComplete="name" value={f.name} onChange={set('name')} required />
      <Input label="Email address" type="email" autoComplete="email" value={f.email} onChange={set('email')} required />
      <Input
        label="Password"
        type="password"
        autoComplete="new-password"
        hint="Minimum 6 characters"
        value={f.password}
        onChange={set('password')}
        required
      />
      <Select
        label="I am a…"
        value={f.role}
        onChange={set('role')}
        options={[
          { value: 'student', label: 'Student' },
          { value: 'mentor', label: 'Mentor (needs admin verification)' },
        ]}
      />
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <Button type="submit" variant="primary" size="lg" icon={UserPlus} loading={busy} disabled={!f.name || !f.email || !f.password}>
        Create account
      </Button>
    </form>
  )
}

function Demo({ onDone }) {
  const { login } = useAuth()
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState('')
  const go = async (email) => {
    setError('')
    setBusy(email)
    try {
      onDone(await login(email, DEMO_PASSWORD))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }
  return (
    <div>
      <p className="muted" style={{ marginBottom: 8 }}>
        Pre-seeded accounts to explore the platform instantly. Password for all three: <code>{DEMO_PASSWORD}</code>
      </p>
      {DEMOS.map((d) => (
        <div className="demo-row" key={d.email}>
          <div className="row" style={{ flexWrap: 'nowrap', minWidth: 0 }}>
            <span className="feature-icon" style={{ margin: 0, width: 38, height: 38, flexShrink: 0 }}>
              <d.icon size={18} aria-hidden="true" />
            </span>
            <div style={{ minWidth: 0 }}>
              <strong>{d.role}</strong> <span className="faint break">{d.email}</span>
              <div className="faint">{d.text}</div>
            </div>
          </div>
          <Button size="sm" loading={busy === d.email} disabled={!!busy} onClick={() => go(d.email)}>
            Sign in
          </Button>
        </div>
      ))}
      {error && (
        <p className="field-error" role="alert" style={{ marginTop: 10 }}>
          {error}
        </p>
      )}
      <Badge tone="warn" className="mt">
        Change these credentials before any real deployment
      </Badge>
    </div>
  )
}

export default function Login() {
  const [params] = useSearchParams()
  const [tab, setTab] = useState(['login', 'register', 'demo'].includes(params.get('tab')) ? params.get('tab') : 'login')
  const navigate = useNavigate()
  const done = (user) => navigate(homeFor(user.role), { replace: true })

  return (
    <div className="auth">
      <div className="hero-layer hero-grid" aria-hidden="true" />
      <div className="hero-layer hero-orbs" aria-hidden="true">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
      </div>
      <SlideUp>
        <Card className="auth-card" spotlight={false}>
          <Link to="/" className="row" style={{ color: 'var(--text-2)', fontSize: 13 }}>
            <ArrowLeft size={14} aria-hidden="true" /> Back to home
          </Link>
          <div className="brand" style={{ padding: '18px 0 0' }}>
            <BrandMark />
            <span>
              SkillVerse
              <small>Learn. Earn. Connect. Grow.</small>
            </span>
          </div>
          <h1>{tab === 'register' ? 'Create your account' : tab === 'demo' ? 'Demo accounts' : 'Welcome back'}</h1>
          <p className="muted" style={{ marginBottom: 20 }}>
            {tab === 'register' ? 'Join as a student or a mentor.' : 'Sign in to continue to your workspace.'}
          </p>
          <div className="tab-gap">
            <Tabs
              label="Account"
              value={tab}
              onChange={setTab}
              tabs={[
                { value: 'login', label: 'Sign in' },
                { value: 'register', label: 'Register' },
                { value: 'demo', label: 'Demo accounts' },
              ]}
            />
          </div>
          {tab === 'login' && <SignIn onDone={done} />}
          {tab === 'register' && <Register onCreated={() => setTab('login')} />}
          {tab === 'demo' && <Demo onDone={done} />}
        </Card>
      </SlideUp>
    </div>
  )
}

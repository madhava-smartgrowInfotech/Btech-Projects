import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileLock2, KeyRound, Play, ShieldCheck, UsersRound } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { DEMO_ACCOUNTS, prepareDemo } from '../lib/demo'
import { BrandMark, Button, Input, Tabs, useToast } from '../components/ui'
import { FadeIn } from '../components/motion'

const POINTS = [
  [FileLock2, 'Encrypted before upload', 'AES-256-GCM runs in your browser. The server stores ciphertext only.'],
  [KeyRound, 'Your key, your password', 'Your RSA private key is wrapped with a PBKDF2-derived key. There is no recovery by design.'],
  [UsersRound, 'Share without exposing keys', 'File keys are re-wrapped for each recipient locally, with Owner, Editor and Viewer roles.'],
  [ShieldCheck, 'Tamper-evident audit trail', 'Every sensitive action is recorded in a hash-chained log you can verify.'],
]

export default function Auth({ mode }) {
  const { user, login, register } = useAuth()
  const navigate = useNavigate()
  const loc = useLocation()
  const toast = useToast()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)
  const [demoBusy, setDemoBusy] = useState(null)
  const [step, setStep] = useState('')
  const dest = loc.state?.from?.startsWith('/app') ? loc.state.from : '/app'

  useEffect(() => {
    document.title = `${mode === 'login' ? 'Sign in' : 'Create account'} · CipherVault`
    setErrors({})
    setFormError('')
  }, [mode])

  if (user && !busy && !demoBusy) return <Navigate to="/app" replace />

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (mode === 'register' && !form.name.trim()) errs.name = 'Enter your name.'
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) errs.email = 'Enter a valid email address.'
    if (mode === 'register' && form.password.length < 8) errs.password = 'Use at least 8 characters.'
    if (mode === 'login' && !form.password) errs.password = 'Enter your password.'
    if (mode === 'register' && form.confirm !== form.password) errs.confirm = 'Passwords do not match.'
    setErrors(errs)
    setFormError('')
    if (Object.keys(errs).length) return
    setBusy(true)
    try {
      if (mode === 'login') await login(form.email.trim(), form.password)
      else await register({ name: form.name.trim(), email: form.email.trim(), password: form.password })
      toast({ title: mode === 'login' ? 'Signed in' : 'Account created', message: 'Your vault is unlocked for this session.' })
      navigate(dest, { replace: true })
    } catch (err) {
      setFormError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const demo = async (key) => {
    setDemoBusy(key)
    setFormError('')
    try {
      await prepareDemo(setStep)
      setStep('Signing in')
      await login(DEMO_ACCOUNTS[key].email, DEMO_ACCOUNTS[key].password)
      toast({ title: `Signed in as demo ${DEMO_ACCOUNTS[key].label.toLowerCase()}`, message: 'Synthetic data only. Nothing here is real.' })
      navigate('/app', { replace: true })
    } catch (err) {
      setFormError(`Demo could not start: ${err.message}`)
    } finally {
      setDemoBusy(null)
      setStep('')
    }
  }

  return (
    <div className="auth-page">
      <aside className="auth-aside">
        <Link to="/" className="brand" style={{ padding: 0 }}>
          <BrandMark />
          <span>
            CipherVault
            <small>Encrypted file storage</small>
          </span>
        </Link>
        <div>
          <h2>
            Files only <span className="text-grad">you</span> can read.
          </h2>
          <p className="muted">Zero-knowledge storage with role-based sharing. Even a stolen database reveals nothing.</p>
          <ul className="auth-points">
            {POINTS.map(([Icon, title, body]) => (
              <li key={title}>
                <Icon size={18} aria-hidden="true" />
                <span>
                  <strong>{title}</strong>
                  <br />
                  <span className="faint">{body}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <span className="faint">AES-256-GCM · RSA-2048-OAEP · PBKDF2 · SHA-256</span>
      </aside>

      <main className="auth-main" id="main">
        <FadeIn className="auth-box">
          <Link to="/" className="row" style={{ gap: 6, fontSize: 14 }}>
            <ArrowLeft size={15} aria-hidden="true" /> Back to home
          </Link>
          <h1>{mode === 'login' ? 'Welcome back' : 'Create your vault'}</h1>
          <p className="muted" style={{ marginBottom: 20 }}>
            {mode === 'login' ? 'Sign in to unlock your encrypted files.' : 'Your browser generates an RSA-2048 key pair and protects the private key with your password.'}
          </p>
          <Tabs
            label="Account"
            value={mode}
            onChange={(v) => navigate(v === 'login' ? '/login' : '/register', { state: loc.state })}
            tabs={[
              { value: 'login', label: 'Sign in' },
              { value: 'register', label: 'Register' },
            ]}
          />
          <form onSubmit={submit} className="stack mt" noValidate>
            {mode === 'register' && <Input label="Full name" autoComplete="name" value={form.name} onChange={set('name')} error={errors.name} />}
            <Input label="Email" type="email" autoComplete="email" value={form.email} onChange={set('email')} error={errors.email} placeholder="you@example.com" />
            <Input
              label="Password"
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={form.password}
              onChange={set('password')}
              error={errors.password}
              hint={mode === 'register' ? 'Minimum 8 characters. It protects your private key - it cannot be recovered.' : undefined}
            />
            {mode === 'register' && <Input label="Confirm password" type="password" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} error={errors.confirm} />}
            {formError && (
              <div className="callout danger" role="alert">
                <ShieldCheck size={18} aria-hidden="true" />
                <span>{formError}</span>
              </div>
            )}
            <Button variant="primary" size="lg" type="submit" loading={busy} disabled={!!demoBusy}>
              {busy ? (mode === 'register' ? 'Generating keys…' : 'Unlocking…') : mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>

          <section className="demo-box" aria-labelledby="demo-h">
            <h3 id="demo-h">Try the demo</h3>
            <p className="faint">Fictional accounts with synthetic files, created on first use. Pick a role to see what it can do.</p>
            <div className="row mt" style={{ flexWrap: 'wrap' }}>
              {Object.entries(DEMO_ACCOUNTS).map(([key, a]) => (
                <Button key={key} size="sm" icon={Play} loading={demoBusy === key} disabled={busy || (!!demoBusy && demoBusy !== key)} onClick={() => demo(key)}>
                  {a.label}
                </Button>
              ))}
            </div>
            <div className="demo-progress" role="status" aria-live="polite">
              {demoBusy ? `${step || 'Starting'}…` : null}
            </div>
            <p className="faint" style={{ marginTop: 10, fontSize: 12.5 }}>
              owner@example.com / Demo-Owner-123 · editor@example.com / Demo-Editor-123 · viewer@example.com / Demo-Viewer-123
            </p>
          </section>
        </FadeIn>
      </main>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Eye, KeyRound, LogIn, Moon, ShieldCheck, Sparkles, Sun } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useDocTitle } from '../lib/hooks'
import { Badge, Brand, Button, Card, Input, KeyValueList, Skeleton, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'
import { useTheme } from '../lib/theme'

export default function Login() {
  useDocTitle('Sign in · VeriVision AI')
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const toast = useToast()
  const { theme, toggle } = useTheme()
  const [demo, setDemo] = useState({ loading: true, data: null })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const ac = new AbortController()
    api
      .config(ac.signal)
      .then((c) => setDemo({ loading: false, data: c.demo_account }))
      .catch((e) => e.name !== 'AbortError' && setDemo({ loading: false, data: null }))
    return () => ac.abort()
  }, [])

  if (user) return <Navigate to={loc.state?.from || '/app'} replace />

  const submit = async (em, pw) => {
    setBusy(true)
    setError('')
    try {
      const u = await login(em, pw)
      toast({ kind: 'success', title: 'Signed in', message: `Welcome, ${u.name || u.email}.` })
      nav(loc.state?.from || '/app', { replace: true })
    } catch (e) {
      setError(e.status === 0 ? 'Cannot reach the API. Start it with run.bat (port 8414) and try again.' : e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="landing" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '24px 16px', position: 'relative', overflow: 'hidden' }}>
      <Blobs preset="hero" />
      <a className="skip-link" href="#signin">Skip to sign in</a>
      <div style={{ position: 'absolute', top: 16, right: 16, zIndex: 2 }}>
        <button type="button" className="icon-btn" onClick={toggle} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} aria-pressed={theme === 'dark'}>
          {theme === 'dark' ? <Sun size={20} aria-hidden="true" /> : <Moon size={20} aria-hidden="true" />}
        </button>
      </div>
      <SlideUp style={{ position: 'relative', zIndex: 1, width: 'min(960px, 100%)' }}>
        <div className="grid-2" style={{ alignItems: 'stretch' }}>
          <Card hover={false} className="stack" id="signin" style={{ '--gap': '18px' }}>
            <Brand />
            <div>
              <h1 style={{ fontSize: 28 }}>Welcome back</h1>
              <p className="muted" style={{ marginTop: 6 }}>Sign in to check whether an image is real or AI-generated.</p>
            </div>
            <form
              className="stack"
              style={{ '--gap': '16px' }}
              onSubmit={(e) => {
                e.preventDefault()
                submit(email.trim(), password)
              }}
              noValidate
            >
              <Input label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="demo@verivision.ai" required />
              <Input label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required error={error || undefined} />
              <Button type="submit" size="lg" block loading={busy} icon={LogIn} disabled={!email || !password}>
                Sign in
              </Button>
            </form>
            <p className="small muted">
              <Link to="/" style={{ color: 'var(--lavender-ink)', fontWeight: 600 }}>← Back to the landing page</Link>
            </p>
          </Card>

          <Card hover={false} tint="lavender" className="stack" style={{ '--gap': '16px' }}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <Badge tone="lavender" icon={Sparkles}>Demo account</Badge>
              <Badge tone="mint" icon={ShieldCheck}>Local only</Badge>
            </div>
            <h2>Try it without signing up</h2>
            <p style={{ color: 'var(--text-2)' }}>
              VeriVision AI runs on this machine. The demo account is built in so you can explore the full analyzer straight away.
            </p>
            {demo.loading ? (
              <div className="stack" style={{ '--gap': '10px' }} role="status" aria-label="Loading demo account">
                <Skeleton height={20} />
                <Skeleton height={20} />
              </div>
            ) : demo.data ? (
              <>
                <KeyValueList items={[['Email', demo.data.email], ['Password', demo.data.password]]} />
                <Button
                  variant="secondary"
                  block
                  icon={KeyRound}
                  loading={busy}
                  onClick={() => {
                    setEmail(demo.data.email)
                    setPassword(demo.data.password)
                    submit(demo.data.email, demo.data.password)
                  }}
                >
                  Use demo account
                </Button>
              </>
            ) : (
              <p className="small" role="alert" style={{ color: 'var(--rose-ink)' }}>
                The API is not reachable, so the demo credentials could not be loaded. Start it with run.bat (port 8414).
              </p>
            )}
            <p className="tiny muted" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Eye size={14} aria-hidden="true" /> Images are analyzed locally and never sent to an external service.
            </p>
          </Card>
        </div>
      </SlideUp>
    </div>
  )
}

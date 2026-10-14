import { ArrowLeft, KeyRound, LogIn, UserPlus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import api, { describeError } from '../api'
import { SlideUp } from '../components/motion'
import Backdrop from '../components/reactbits/Backdrop'
import { Button, Input } from '../components/ui/controls'
import { StatusDot } from '../components/ui/display'
import { ErrorState, useToast } from '../components/ui/feedback'
import Logo from '../components/ui/Logo'
import { Tabs } from '../components/ui/nav'
import Typewriter from '../components/ui/Typewriter'
import { useAuth } from '../lib/auth'

const DEMO = { email: 'demo@taxsentinel.app', password: 'Demo@1234' }

function HealthLines() {
  const [h, setH] = useState(null)
  const [down, setDown] = useState(false)
  useEffect(() => { api.get('/health').then((r) => setH(r.data)).catch(() => setDown(true)) }, [])
  const row = (k, ok, v) => (
    <div className="flex items-center justify-between gap-4">
      <span className="text-dim">{k}</span>
      <span className="flex items-center gap-2" style={{ color: ok ? 'var(--ok)' : 'var(--warn)' }}><StatusDot tone={ok ? 'ok' : 'warn'} />{v}</span>
    </div>
  )
  return (
    <div className="space-y-1.5 font-mono text-[12px]">
      {down ? row('api :8105', false, 'unreachable') : !h ? <div className="text-dim">checking api…</div> : (
        <>
          {row('api :8105', true, 'online')}
          {row('pipeline', h.pipeline_ready, h.pipeline_ready ? 'ready' : 'loading')}
          {row('gemini', h.gemini_configured, h.gemini_configured ? 'configured' : 'not configured')}
        </>
      )}
    </div>
  )
}

export default function Login() {
  const [params] = useSearchParams()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState(params.get('demo') ? { name: '', ...DEMO } : { name: '', email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const body = mode === 'login' ? { email: form.email, password: form.password } : form
      const { data } = await api.post(`/auth/${mode}`, body)
      signIn(data.token, data.user)
      toast({ tone: 'ok', title: mode === 'login' ? `Signed in as ${data.user.name}` : `Account created for ${data.user.name}` })
      navigate(location.state?.from || '/app', { replace: true })
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="relative grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <aside className="relative hidden overflow-hidden border-r border-line bg-panel/40 lg:flex lg:flex-col lg:justify-between lg:p-10">
        <Backdrop intensity={1.3} className="absolute inset-0 fade-mask" />
        <Link to="/" className="relative z-[1]"><Logo /></Link>
        <div className="relative z-[1] max-w-md">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-ok">// secure session</div>
          <Typewriter as="h2" text="> authenticate --role analyst" className="mt-3 font-mono text-2xl font-semibold text-fg" keepCaret />
          <p className="mt-4 text-sm text-muted">Sign in to rank taxpayers by ITC-fraud risk, trace circular-trading rings and generate cited case notes.</p>
          <div className="panel scan mt-8 p-4"><div className="relative z-[1]"><HealthLines /></div></div>
        </div>
        <p className="relative z-[1] font-mono text-[11px] text-dim">Sample data · synthetic GST ecosystem</p>
      </aside>

      <main className="flex items-center justify-center p-4 sm:p-8">
        <SlideUp className="w-full max-w-sm">
          <div className="mb-8 flex items-center justify-between lg:hidden">
            <Link to="/"><Logo /></Link>
            <Link to="/" className="inline-flex items-center gap-1 font-mono text-[11px] uppercase text-muted hover:text-ok"><ArrowLeft size={13} /> Home</Link>
          </div>
          <h1 className="font-mono text-xl font-semibold text-fg">{mode === 'login' ? 'Sign in' : 'Create an account'}</h1>
          <p className="mt-1 text-sm text-muted">{mode === 'login' ? 'Welcome back, analyst.' : 'Takes ten seconds. Passwords need 8+ characters.'}</p>
          <div className="mt-6">
            <Tabs id="auth" label="Sign in or register" value={mode} onChange={(m) => { setMode(m); setError(null) }}
              tabs={[{ id: 'login', label: 'Sign in' }, { id: 'register', label: 'Create account' }]} />
          </div>
          <form onSubmit={submit} className="mt-5 space-y-4" id={`auth-${mode}-panel`} role="tabpanel" aria-labelledby={`auth-${mode}`}>
            {mode === 'register' && <Input label="Full name" value={form.name} onChange={set('name')} required autoComplete="name" />}
            <Input label="Email" type="email" value={form.email} onChange={set('email')} required autoComplete="email" />
            <Input label="Password" type="password" value={form.password} onChange={set('password')} required
              minLength={mode === 'register' ? 8 : undefined} autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              hint={mode === 'register' ? 'At least 8 characters' : undefined} />
            <ErrorState error={error} title={mode === 'login' ? 'Sign-in failed' : 'Could not create the account'} compact />
            <Button type="submit" size="lg" loading={busy} icon={mode === 'login' ? LogIn : UserPlus} className="w-full">
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>
          {mode === 'login' && (
            <button type="button" onClick={() => setForm({ ...form, ...DEMO })}
              className="mt-4 flex w-full items-center gap-3 rounded-[6px] border border-dashed border-line-strong p-3 text-left text-xs text-muted transition-colors hover:border-ok/60 hover:text-fg">
              <KeyRound size={15} className="shrink-0 text-ok" aria-hidden="true" />
              <span>Demo account <b className="font-mono text-fg">{DEMO.email}</b> / <b className="font-mono text-fg">{DEMO.password}</b> <span className="text-ok">- click to fill</span></span>
            </button>
          )}
        </SlideUp>
      </main>
    </div>
  )
}

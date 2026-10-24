import { ArrowLeft, KeyRound, LogIn } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import api, { describeError } from '../api'
import { Logo } from '../components/ui/AppShell'
import { Button, IconButton, Input } from '../components/ui/controls'
import { Card } from '../components/ui/display'
import { ErrorState } from '../components/ui/feedback'
import Backdrop from '../components/reactbits/Backdrop'
import { SlideUp } from '../components/motion'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'
import { Moon, Sun } from 'lucide-react'

export default function Login() {
  const { user, signIn } = useAuth()
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()
  const loc = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [demo, setDemo] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const target = loc.state?.from && loc.state.from.startsWith('/app') ? loc.state.from : '/app'

  useEffect(() => { api.get('/auth/demo', { silent: true }).then((r) => setDemo(r.data)).catch(() => {}) }, [])
  if (user) return <Navigate to={target} replace />

  async function submit(e, creds) {
    e?.preventDefault()
    const em = creds?.email ?? email
    const pw = creds?.password ?? password
    setBusy(true)
    setError(null)
    try {
      await signIn(em, pw)
      navigate(target, { replace: true })
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative grid min-h-screen place-items-center overflow-hidden px-4 py-10">
      <Backdrop className="absolute inset-0" />
      <div className="absolute left-4 top-4 flex w-[calc(100%-2rem)] items-center justify-between">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted hover:text-ok"><ArrowLeft size={15} aria-hidden="true" />Back</Link>
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
      </div>
      <SlideUp className="relative z-10 w-full max-w-md">
        <div className="mb-6 flex justify-center"><Logo /></div>
        <Card title="Sign in to the control room">
          <form onSubmit={submit} className="space-y-4" noValidate>
            <Input label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="operator@flowsense.app" required />
            <Input label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
            {error && <ErrorState error={error} compact title="Sign-in failed" />}
            <Button type="submit" icon={LogIn} loading={busy} className="w-full" disabled={!email || !password}>Sign in</Button>
          </form>
          {demo && (
            <div className="mt-5 rounded-[6px] border border-dashed border-line-strong bg-panel-2 p-3">
              <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-dim"><KeyRound size={12} aria-hidden="true" />Demo account</div>
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 font-mono text-xs">
                <dt className="text-dim">email</dt><dd className="break-all text-fg">{demo.email}</dd>
                <dt className="text-dim">password</dt><dd className="text-fg">{demo.password}</dd>
              </dl>
              <Button variant="secondary" size="sm" className="mt-3 w-full" loading={busy}
                onClick={() => { setEmail(demo.email); setPassword(demo.password); submit(null, demo) }}>Use demo account</Button>
            </div>
          )}
        </Card>
      </SlideUp>
    </div>
  )
}

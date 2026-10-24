import { KeyRound } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import Backdrop from '../components/reactbits/Backdrop'
import { SlideUp } from '../components/motion'
import Logo from '../components/ui/Logo'
import { Button, Input } from '../components/ui/controls'
import { DEMO_USER, useAuth } from '../lib/auth'

export default function Login() {
  const { user, signIn } = useAuth()
  const navigate = useNavigate()
  const loc = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [fieldErr, setFieldErr] = useState({})

  if (user) return <Navigate to={loc.state?.from || '/app'} replace />

  function submit(e) {
    e.preventDefault()
    const fe = {}
    if (!email.trim()) fe.email = 'Enter your email.'
    if (!password) fe.password = 'Enter your password.'
    setFieldErr(fe)
    if (Object.keys(fe).length) return
    const r = signIn(email, password)
    if (!r.ok) { setError(r.error); return }
    navigate(loc.state?.from || '/app', { replace: true })
  }

  function fillDemo() {
    setEmail(DEMO_USER.email)
    setPassword(DEMO_USER.password)
    setError('')
    setFieldErr({})
  }

  return (
    <main className="relative grid min-h-screen place-items-center overflow-hidden px-4 py-10">
      <Backdrop className="absolute inset-0 opacity-60" intensity={0.8} />
      <SlideUp className="relative z-[1] w-full max-w-md">
        <Link to="/" className="mb-6 inline-block"><Logo /></Link>
        <div className="panel scan p-6">
          <div className="relative z-[1]">
            <h1 className="font-mono text-xl font-semibold text-fg">Sign in to the console</h1>
            <p className="mt-1 text-sm text-muted">SentinelFlow runs on this machine only. Use the demo account below.</p>
            <form onSubmit={submit} noValidate className="mt-5 space-y-4">
              <Input label="Email" type="email" autoComplete="username" value={email} error={fieldErr.email} onChange={(e) => setEmail(e.target.value)} />
              <Input label="Password" type="password" autoComplete="current-password" value={password} error={fieldErr.password} onChange={(e) => setPassword(e.target.value)} />
              {error && <p role="alert" className="rounded-[6px] border border-alert/40 bg-alert/10 p-2.5 text-sm text-alert">{error}</p>}
              <Button type="submit" size="lg" className="w-full">Sign in</Button>
            </form>
            <div className="mt-5 rounded-[6px] border border-line-strong bg-panel-2 p-3 font-mono text-xs text-muted">
              <div className="mb-1 text-[10px] uppercase tracking-[0.14em] text-dim">Demo account</div>
              <div>{DEMO_USER.email}</div>
              <div>{DEMO_USER.password}</div>
              <Button type="button" variant="secondary" size="sm" icon={KeyRound} className="mt-2" onClick={fillDemo}>Fill demo credentials</Button>
            </div>
          </div>
        </div>
      </SlideUp>
    </main>
  )
}

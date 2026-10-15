import { LogIn, Moon, Sun, UserPlus } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { describeError } from '../api'
import { SlideUp } from '../components/motion'
import Backdrop from '../components/reactbits/Backdrop'
import Logo from '../components/ui/Logo'
import { Button, IconButton, Input } from '../components/ui/controls'
import { Card } from '../components/ui/display'
import { ErrorState, useToast } from '../components/ui/feedback'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'

const DEMO = { email: 'demo@signbridge.app', password: 'demo1234' }

export default function Auth({ mode }) {
  const register = mode === 'register'
  const { user, signIn, register: signUp } = useAuth()
  const { theme, toggle } = useTheme()
  const toast = useToast()
  const navigate = useNavigate()
  const from = useLocation().state?.from || '/app'
  const [name, setName] = useState('')
  const [email, setEmail] = useState(register ? '' : DEMO.email)
  const [password, setPassword] = useState(register ? '' : DEMO.password)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  if (user) return <Navigate to={from} replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const u = register ? await signUp(name.trim(), email.trim(), password) : await signIn(email.trim(), password)
      toast({ tone: 'ok', title: register ? 'Account created' : 'Signed in', body: `Welcome, ${u.name}.` })
      navigate(from, { replace: true })
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative grid min-h-screen place-items-center overflow-hidden px-4 py-10">
      <Backdrop intensity={0.7} className="absolute inset-0 opacity-80" />
      <div className="absolute right-4 top-4 z-10">
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
      </div>
      <SlideUp className="relative z-[1] w-full max-w-md">
        <div className="mb-6 flex justify-center"><Link to="/" aria-label="SignBridge home"><Logo /></Link></div>
        <Card title={register ? 'create account' : 'sign in'} bodyClass="p-5">
          <form onSubmit={submit} className="space-y-4" noValidate>
            {register && <Input label="Name" autoComplete="name" required value={name} onChange={(e) => setName(e.target.value)} />}
            <Input label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            <Input label="Password" type="password" autoComplete={register ? 'new-password' : 'current-password'} required minLength={register ? 6 : undefined}
              hint={register ? 'At least 6 characters.' : undefined} value={password} onChange={(e) => setPassword(e.target.value)} />
            {error && <ErrorState compact title={register ? 'Could not create account' : 'Could not sign in'} error={error} />}
            <Button type="submit" size="lg" className="w-full" icon={register ? UserPlus : LogIn} loading={busy}
              disabled={!email || !password || (register && !name.trim())}>
              {register ? 'Create account' : 'Sign in'}
            </Button>
          </form>
          {!register && (
            <p className="mt-4 rounded-[6px] border border-dashed border-line-strong p-3 font-mono text-[11px] leading-relaxed text-muted">
              demo account · <span className="text-fg">{DEMO.email}</span> / <span className="text-fg">{DEMO.password}</span> (pre-filled)
            </p>
          )}
          <p className="mt-4 text-center text-sm text-muted">
            {register ? <>Already have an account? <Link className="text-ok underline" to="/login">Sign in</Link></>
              : <>New here? <Link className="text-ok underline" to="/register">Create an account</Link></>}
          </p>
        </Card>
      </SlideUp>
    </div>
  )
}

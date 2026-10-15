import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { describeError, setSession } from '../api'
import Logo from '../components/ui/Logo'
import { Button, Input } from '../components/ui/controls'
import { ErrorState } from '../components/ui/feedback'
import { Card } from '../components/ui/display'
import { Tabs } from '../components/ui/nav'
import { useToast } from '../components/ui/feedback'
import { logEvent } from '../lib/activity'
import { FadeIn } from '../components/motion'

const TABS = [{ id: 'login', label: 'Sign in' }, { id: 'register', label: 'Create account' }]

export default function Login() {
  const nav = useNavigate()
  const toast = useToast()
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('Demo@12345')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { data } = await api.post(`/auth/${mode}`, { username, password })
      setSession(data.token, data.username)
      logEvent('auth', `${mode === 'login' ? 'signed in' : 'account created'} as ${data.username}`)
      toast({ tone: 'ok', title: mode === 'login' ? 'Signed in' : 'Account created', body: `Welcome, ${data.username}` })
      nav('/keys')
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-screen place-items-center px-4 py-10">
      <FadeIn className="w-full max-w-sm">
        <div className="mb-6 flex justify-center"><Link to="/" aria-label="cipher veil home"><Logo /></Link></div>
        <Card title={mode === 'login' ? 'Sign in' : 'Create an account'} bodyClass="p-5">
          <form onSubmit={submit} className="space-y-4">
            <Tabs id="auth" tabs={TABS} value={mode} label="Sign in or create an account"
              onChange={(m) => { setMode(m); setError(null) }} />
            <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)}
              autoComplete="username" required minLength={3} maxLength={40} hint="3 to 40 letters, digits, dot, dash or underscore" />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={8} maxLength={72}
              hint={mode === 'register' ? 'At least 8 characters' : 'Demo login is pre-filled: demo / Demo@12345'} />
            <ErrorState error={error} />
            <Button type="submit" size="lg" className="w-full" loading={busy}>
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>
        </Card>
        <p className="mt-4 text-center text-xs text-dim">
          <Link to="/" className="hover:text-ok">Back to the overview</Link>
        </p>
      </FadeIn>
    </div>
  )
}

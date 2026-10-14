import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Building2, LayoutDashboard, LogIn, User } from 'lucide-react'
import { describeError } from '../api'
import { homeFor, useAuth } from '../auth'
import { SlideUp } from '../components/motion'
import { Button, Input, Select } from '../components/ui/controls'
import { Card } from '../components/ui/display'
import { ErrorState, useToast } from '../components/ui/feedback'
import { Tabs, TabPanel } from '../components/ui/nav'

const DEMOS = [
  ['patient', User, 'Patient', 'patient@mediqueue.app'],
  ['staff', Building2, 'Hospital desk', 'desk1@mediqueue.app'],
  ['admin', LayoutDashboard, 'District admin', 'admin@mediqueue.app'],
]
const TABS = [
  { id: 'login', label: 'Log in' },
  { id: 'register', label: 'Create patient account' },
]
const GENDER = [
  ['', 'Not stated'],
  ['F', 'Female'],
  ['M', 'Male'],
]

export default function Login() {
  const { login, register } = useAuth()
  const nav = useNavigate()
  const toast = useToast()
  const [params] = useSearchParams()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({
    email: params.get('role') === 'staff' ? 'desk1@mediqueue.app' : '',
    password: '',
    name: '',
    age: '',
    gender: '',
    phone: '',
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const finish = (u) => {
    toast({ tone: 'ok', title: mode === 'login' ? `Signed in as ${u.name}` : 'Account created', body: 'Opening your workspace' })
    nav(homeFor(u))
  }

  const submit = async (e) => {
    e?.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const u =
        mode === 'login'
          ? await login(form.email, form.password)
          : await register({
              name: form.name,
              email: form.email,
              password: form.password,
              age: form.age ? Number(form.age) : null,
              gender: form.gender || null,
              phone: form.phone || null,
            })
      finish(u)
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  const demo = async (email) => {
    setBusy(true)
    setError(null)
    try {
      finish(await login(email, 'demo1234'))
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-5">
      <SlideUp>
        <Card title={mode === 'login' ? 'Sign in' : 'New patient account'} eyebrow="MediQueue - OP booking">
          <Tabs id="auth" tabs={TABS} value={mode} onChange={(m) => { setMode(m); setError(null) }} label="Log in or register" />
          <TabPanel tabsId="auth" value={mode}>
            <form onSubmit={submit} className="mt-5 space-y-4" noValidate={false}>
              {mode === 'register' && (
                <>
                  <Input label="Full name" value={form.name} onChange={set('name')} required minLength={2} autoComplete="name" />
                  <div className="grid grid-cols-3 gap-2">
                    <Input label="Age" type="number" min="0" max="120" value={form.age} onChange={set('age')} />
                    <Select label="Gender" options={GENDER} value={form.gender} onChange={set('gender')} />
                    <Input label="Phone" type="tel" value={form.phone} onChange={set('phone')} autoComplete="tel" />
                  </div>
                </>
              )}
              <Input label="Email" type="email" value={form.email} onChange={set('email')} required autoComplete="username" />
              <Input
                label="Password"
                type="password"
                value={form.password}
                onChange={set('password')}
                required
                minLength={mode === 'register' ? 6 : 1}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                hint={mode === 'register' ? 'At least 6 characters' : undefined}
              />
              <ErrorState error={error} />
              <Button type="submit" icon={LogIn} loading={busy} className="w-full" size="lg">
                {mode === 'login' ? 'Log in' : 'Create account'}
              </Button>
            </form>
          </TabPanel>
        </Card>
      </SlideUp>

      <SlideUp delay={0.1}>
        <Card title="Demo accounts" eyebrow="password demo1234">
          <p className="mb-4 text-xs text-muted">
            Each hospital has an OP desk login: <span className="font-mono text-fg">desk&lt;id&gt;@mediqueue.app</span>.
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {DEMOS.map(([key, Icon, label, email]) => (
              <button
                key={key}
                type="button"
                disabled={busy}
                onClick={() => demo(email)}
                className="flex flex-col items-center gap-2 rounded-[6px] border border-line-strong bg-panel-2 px-3 py-4 font-mono text-[11px] uppercase tracking-[0.1em] text-muted transition-colors hover:border-ok/60 hover:text-fg disabled:opacity-50"
              >
                <Icon size={18} className="text-ok" aria-hidden="true" />
                {label}
              </button>
            ))}
          </div>
        </Card>
      </SlideUp>
    </div>
  )
}

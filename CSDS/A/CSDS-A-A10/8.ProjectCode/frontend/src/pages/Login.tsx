import { type FormEvent, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, ArrowRight, Loader2, Lock, Mail } from 'lucide-react'
import { Navigate, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Input, Label } from '@/components/ui/Input'
import { login } from '@/lib/api'
import { ROLE_HOME, useAuth } from '@/store/auth'
import { toast } from '@/store/toast'

const DEMO_ACCOUNTS = [
  { role: 'Administrator', email: 'admin@medflow.app', password: 'Admin@123' },
  { role: 'Doctor · General Medicine', email: 'dr.mehta@medflow.app', password: 'Doctor@123' },
  { role: 'Nurse · Ward', email: 'nurse.iyer@medflow.app', password: 'Nurse@123' },
  { role: 'Lab Technician', email: 'lab.singh@medflow.app', password: 'Lab@123' },
  { role: 'Reception', email: 'reception.kaur@medflow.app', password: 'Reception@123' },
]

export default function Login() {
  const user = useAuth((s) => s.user)
  const setSession = useAuth((s) => s.setSession)
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (user) return <Navigate to={ROLE_HOME[user.role]} replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await login(email, password)
      setSession(data.user, data.access_token)
      toast({ title: `Welcome back, ${data.user.name.split(' ')[0]}`, variant: 'success' })
      navigate(ROLE_HOME[data.user.role])
    } catch {
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-ink-950 bg-grid px-4">
      <div className="pointer-events-none absolute left-1/2 top-0 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-brand-500/10 blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 grid w-full max-w-4xl overflow-hidden rounded-3xl border border-white/8 bg-ink-900/60 shadow-2xl backdrop-blur-xl md:grid-cols-2"
      >
        {/* Left: brand panel */}
        <div className="relative hidden flex-col justify-between bg-gradient-to-br from-brand-600 via-brand-700 to-ink-900 p-10 md:flex">
          <div className="absolute inset-0 bg-grid opacity-20" />
          <div className="relative flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
              <Activity size={19} className="text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display text-lg font-bold text-white">MedFlow</span>
          </div>
          <div className="relative">
            <h2 className="font-display text-2xl font-bold leading-tight text-white text-balance">
              Real-time patient flow, from registration to discharge.
            </h2>
            <p className="mt-3 text-sm text-brand-100/80">
              Digital tokens, live bed availability and AI-prioritised queues — one platform for
              every department.
            </p>
            <div className="mt-6 flex -space-x-2">
              {['#f59e0b', '#10b981', '#0891b2', '#ec4899'].map((c) => (
                <div
                  key={c}
                  className="h-8 w-8 rounded-full border-2 border-brand-700"
                  style={{ background: c }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right: form */}
        <div className="p-8 sm:p-10">
          <h1 className="font-display text-xl font-bold text-white">Sign in to your workspace</h1>
          <p className="mt-1 text-sm text-ink-400">Use your staff credentials to continue.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <Label htmlFor="email">Email address</Label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500" />
                <Input
                  id="email"
                  type="email"
                  required
                  autoComplete="username"
                  placeholder="you@medflow.app"
                  className="pl-9"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500" />
                <Input
                  id="password"
                  type="password"
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="pl-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400"
              >
                {error}
              </motion.p>
            )}

            <Button type="submit" size="lg" disabled={loading} className="w-full">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>

          <div className="mt-6 rounded-xl border border-white/8 bg-ink-950/60 p-3.5">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
              Demo accounts
            </p>
            <div className="space-y-1.5">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => {
                    setEmail(acc.email)
                    setPassword(acc.password)
                  }}
                  className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-xs transition-colors hover:bg-white/5"
                >
                  <span className="text-ink-300">{acc.role}</span>
                  <span className="font-mono text-ink-500">{acc.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

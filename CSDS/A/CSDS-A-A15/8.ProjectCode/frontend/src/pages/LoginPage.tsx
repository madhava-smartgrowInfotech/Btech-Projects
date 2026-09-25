import { motion } from 'framer-motion'
import { AlertCircle, ScanEye } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input, Label } from '@/components/ui/Input'
import { useAuth } from '@/context/AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('demo@visionforge.ai')
  const [password, setPassword] = useState('demo1234')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/app/dashboard')
    } catch {
      setError('Invalid email or password. Try the demo account below, or sign up.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#05070c] bg-grid px-6">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md glass-card rounded-2xl p-8"
      >
        <Link to="/" className="flex items-center gap-2 font-display font-semibold text-white mb-8">
          <ScanEye className="h-5 w-5 text-cyan-400" />
          VisionForge <span className="text-gradient">AI</span>
        </Link>

        <h1 className="font-display text-2xl font-bold text-white mb-1">Welcome back</h1>
        <p className="text-sm text-slate-400 mb-6">Sign in to access your inspection dashboard.</p>

        {error && (
          <div className="mb-5 flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>

        <p className="mt-3 text-xs text-slate-500 text-center">
          Demo account pre-filled — just click Sign in.
        </p>

        <p className="mt-6 text-sm text-slate-400 text-center">
          Don&rsquo;t have an account?{' '}
          <Link to="/signup" className="text-cyan-400 hover:text-cyan-300">
            Create one
          </Link>
        </p>
      </motion.div>
    </div>
  )
}

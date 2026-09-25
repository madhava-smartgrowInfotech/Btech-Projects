import { type ReactNode, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  Bed as BedIcon,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  MonitorPlay,
  Stethoscope,
  UserPlus,
} from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { Avatar } from '@/components/ui/Avatar'
import { ROLE_HOME, ROLE_LABELS, useAuth } from '@/store/auth'

const ROLE_ICON: Record<string, ReactNode> = {
  admin: <LayoutDashboard size={18} />,
  doctor: <Stethoscope size={18} />,
  nurse: <BedIcon size={18} />,
  lab_tech: <FlaskConical size={18} />,
  reception: <UserPlus size={18} />,
}

export function AppShell({
  title,
  subtitle,
  children,
  actions,
}: {
  title: string
  subtitle?: string
  children: ReactNode
  actions?: ReactNode
}) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000 * 30)
    return () => clearInterval(timer)
  }, [])

  if (!user) return null

  return (
    <div className="min-h-screen bg-ink-950 bg-grid">
      <div className="pointer-events-none fixed inset-x-0 top-0 h-96 bg-gradient-to-b from-brand-500/10 via-transparent to-transparent" />

      <header className="relative z-10 border-b border-white/5 bg-ink-950/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-3.5">
          <Link to={ROLE_HOME[user.role]} className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-400 to-vital-500 shadow-lg shadow-brand-500/30">
              <Activity size={17} className="text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display text-base font-bold tracking-tight text-white">
              Med<span className="text-brand-400">Flow</span>
            </span>
          </Link>

          <div className="hidden items-center gap-1.5 text-xs font-medium text-ink-400 md:flex">
            {ROLE_ICON[user.role]}
            <span>{ROLE_LABELS[user.role]}</span>
            <span className="mx-2 h-1 w-1 rounded-full bg-ink-600" />
            <span>
              {now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })} ·{' '}
              {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="/board"
              target="_blank"
              rel="noreferrer"
              className="hidden items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-ink-300 hover:bg-white/5 hover:text-white lg:flex"
            >
              <MonitorPlay size={14} />
              Waiting Board
            </a>
            <div className="flex items-center gap-2.5">
              <Avatar name={user.name} color={user.avatar_color} size={32} />
              <div className="hidden text-left sm:block">
                <p className="text-sm font-medium leading-tight text-white">{user.name}</p>
                <p className="text-[11px] leading-tight text-ink-400">{user.specialty || ROLE_LABELS[user.role]}</p>
              </div>
            </div>
            <button
              onClick={() => {
                logout()
                navigate('/login')
              }}
              className="rounded-lg p-2 text-ink-400 transition-colors hover:bg-white/5 hover:text-red-400"
              title="Sign out"
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-[1600px] px-6 py-7">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="mb-6 flex flex-wrap items-end justify-between gap-4"
        >
          <div>
            <h1 className="font-display text-2xl font-bold text-white">{title}</h1>
            {subtitle && <p className="mt-1 text-sm text-ink-400">{subtitle}</p>}
          </div>
          {actions}
        </motion.div>
        {children}
      </main>
    </div>
  )
}

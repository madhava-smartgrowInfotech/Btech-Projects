import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutGrid, History, LineChart, Home } from 'lucide-react'
import { Logo } from '../ui/Logo'

const items = [
  { to: '/app', label: 'Workspace', icon: LayoutGrid },
  { to: '/history', label: 'History', icon: History },
  { to: '/insights', label: 'Insights', icon: LineChart },
]

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation()

  return (
    <div className="min-h-screen flex bg-[var(--color-bg)]">
      <aside className="hidden lg:flex flex-col w-64 shrink-0 border-r border-[var(--color-border-soft)] px-5 py-6 gap-8 sticky top-0 h-screen">
        <Link to="/">
          <Logo />
        </Link>
        <nav className="flex flex-col gap-1">
          {items.map((item) => {
            const active = location.pathname === item.to
            const Icon = item.icon
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  active
                    ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-white/5 border border-transparent'
                }`}
              >
                <Icon size={17} />
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="mt-auto">
          <Link
            to="/"
            className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm text-[var(--color-text-faint)] hover:text-[var(--color-text)] transition-colors"
          >
            <Home size={16} />
            Back to overview
          </Link>
        </div>
      </aside>
      <div className="flex-1 min-w-0">
        <MobileTopBar />
        <main className="px-4 sm:px-8 py-8 max-w-7xl mx-auto">{children}</main>
      </div>
    </div>
  )
}

function MobileTopBar() {
  const location = useLocation()
  return (
    <div className="lg:hidden sticky top-0 z-30 glass border-b border-[var(--color-border-soft)] px-4 py-3 flex items-center justify-between">
      <Link to="/">
        <Logo />
      </Link>
      <nav className="flex gap-1">
        {items.map((item) => {
          const active = location.pathname === item.to
          const Icon = item.icon
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`p-2 rounded-lg ${active ? 'text-emerald-300 bg-emerald-500/10' : 'text-[var(--color-text-muted)]'}`}
            >
              <Icon size={18} />
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

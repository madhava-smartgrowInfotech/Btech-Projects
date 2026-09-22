import { Activity, BarChart3, FilePlus2, Inbox, ListChecks, LogOut } from 'lucide-react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

const LINKS = {
  citizen: [
    { to: '/file', label: 'File a complaint', icon: FilePlus2 },
    { to: '/track', label: 'My complaints', icon: ListChecks },
  ],
  officer: [
    { to: '/queue', label: 'Triage queue', icon: Inbox },
    { to: '/analytics', label: 'Hotspots & analytics', icon: BarChart3 },
  ],
}
LINKS.admin = LINKS.officer

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-700 text-white">
        <Activity className="h-5 w-5" />
      </span>
      CivicPulse
    </Link>
  )
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-[1000] border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <Logo />
          {user && (
            <nav className="flex flex-wrap gap-1">
              {(LINKS[user.role] || []).map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium ${
                      isActive ? 'bg-brand-50 text-brand-800' : 'text-slate-600 hover:bg-slate-100'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
          )}
          <div className="ml-auto flex items-center gap-3">
            {user ? (
              <>
                <div className="text-right text-xs leading-tight">
                  <div className="font-medium text-slate-800">{user.name}</div>
                  <div className="capitalize text-slate-500">{user.role}</div>
                </div>
                <button
                  className="btn-secondary px-2.5"
                  onClick={() => {
                    logout()
                    nav('/login')
                  }}
                  title="Log out"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </>
            ) : (
              <Link to="/login" className="btn-primary">
                Log in
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  )
}

import { NavLink, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { Activity, FileSearch, KeyRound, LogOut, ScrollText, Send, ShieldCheck, ShieldHalf, Download } from 'lucide-react'
import { clearSession, getToken, getUser } from '../api'

const links = [
  ['/keys', 'Keys', KeyRound],
  ['/send', 'Send', Send],
  ['/receive', 'Receive', Download],
  ['/analysis', 'Analysis', FileSearch],
  ['/robustness', 'Robustness', ShieldHalf],
  ['/log', 'Log', ScrollText],
]

export default function Layout() {
  const nav = useNavigate()
  if (!getToken()) return <Navigate to="/login" replace />
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-ink-700 bg-ink-900 text-white">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-2">
          <NavLink to="/keys" className="flex items-center gap-2 font-semibold">
            <ShieldCheck className="h-5 w-5 text-brand-500" /> CipherVeil
          </NavLink>
          <nav className="flex flex-1 gap-1 overflow-x-auto">
            {links.map(([to, label, Icon]) => (
              <NavLink key={to} to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-sm ${
                    isActive ? 'bg-ink-700 text-white' : 'text-slate-300 hover:bg-ink-800'}`}>
                <Icon className="h-4 w-4" /> {label}
              </NavLink>
            ))}
          </nav>
          <span className="hidden items-center gap-1 text-sm text-slate-300 sm:flex"><Activity className="h-4 w-4" /> {getUser()}</span>
          <button className="rounded-md p-2 text-slate-300 hover:bg-ink-800" title="Sign out"
            onClick={() => { clearSession(); nav('/') }}>
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8"><Outlet /></main>
    </div>
  )
}

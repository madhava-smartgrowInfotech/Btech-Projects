import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { BarChart3, GraduationCap, History, LogOut, MessagesSquare, Wifi, WifiOff } from 'lucide-react'
import api from '../api'
import { useAuth } from '../auth.jsx'
import Logo from './Logo.jsx'

const links = [
  { to: '/app', label: 'Conversation', icon: MessagesSquare, end: true },
  { to: '/app/practice', label: 'Practice', icon: GraduationCap },
  { to: '/app/history', label: 'History', icon: History },
  { to: '/app/performance', label: 'Performance', icon: BarChart3 },
]

export function useHealth() {
  const [health, setHealth] = useState(null)
  useEffect(() => {
    let alive = true
    const load = () => api.get('/health').then((r) => alive && setHealth(r.data)).catch(() => alive && setHealth(null))
    load()
    const t = setInterval(load, 15000)
    return () => { alive = false; clearInterval(t) }
  }, [])
  return health
}

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const health = useHealth()
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center gap-6">
          <Logo />
          <nav className="flex gap-1 overflow-x-auto">
            {links.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end}
                className={({ isActive }) => `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon size={16} /> <span className="hidden sm:inline">{label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            {health && (
              <span className={`chip ${health.online ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}
                title={health.online ? 'Online: sentences are polished by Gemini' : 'Offline: everything runs on this device'}>
                {health.online ? <Wifi size={12} /> : <WifiOff size={12} />} {health.online ? 'Online' : 'Offline mode'}
              </span>
            )}
            <span className="text-sm text-slate-500 hidden md:inline">{user?.name}</span>
            <button className="btn-secondary !px-3" onClick={() => { logout(); nav('/') }} title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

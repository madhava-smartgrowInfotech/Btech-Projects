import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { AudioLines, BarChart3, FlaskConical, Gauge, LogOut, PhoneCall } from 'lucide-react'
import { currentUser } from '../api.js'

const links = [
  { to: '/calls', label: 'Calls', icon: PhoneCall },
  { to: '/studio', label: 'Sample studio', icon: FlaskConical },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/performance', label: 'Model performance', icon: Gauge },
]

export default function Layout() {
  const nav = useNavigate()
  const user = currentUser()
  const logout = () => {
    localStorage.removeItem('cs_token')
    localStorage.removeItem('cs_user')
    nav('/login')
  }
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3">
          <NavLink to="/calls" className="flex items-center gap-2 font-bold text-indigo-800">
            <AudioLines className="h-6 w-6" /> CallSense
          </NavLink>
          <nav className="flex flex-1 flex-wrap gap-1">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm ${isActive ? 'bg-indigo-50 font-medium text-indigo-800' : 'text-slate-600 hover:bg-slate-100'}`
                }
              >
                <Icon className="h-4 w-4" /> {label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <div className="text-right leading-tight">
              <div className="font-medium">{user.name}</div>
              <div className="text-xs capitalize text-slate-500">{user.role}</div>
            </div>
            <button className="btn-secondary px-2.5" onClick={logout} title="Sign out">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

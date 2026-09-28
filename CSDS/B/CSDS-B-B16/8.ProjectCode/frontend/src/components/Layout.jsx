import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { BarChart3, Eye, LogOut, PlusCircle, Users } from 'lucide-react'

const links = [
  { to: '/screening/new', label: 'New screening', icon: PlusCircle },
  { to: '/patients', label: 'Patients & history', icon: Users },
  { to: '/performance', label: 'Model performance', icon: BarChart3 },
]

export default function Layout() {
  const nav = useNavigate()
  const user = JSON.parse(localStorage.getItem('rg_user') || '{}')
  const logout = () => {
    localStorage.removeItem('rg_token')
    localStorage.removeItem('rg_user')
    nav('/login')
  }
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3">
          <NavLink to="/screening/new" className="flex items-center gap-2 font-bold text-teal-800">
            <Eye className="h-6 w-6" /> RetinaGuard
          </NavLink>
          <nav className="flex flex-1 flex-wrap gap-1">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm ${isActive ? 'bg-teal-50 font-medium text-teal-800' : 'text-slate-600 hover:bg-slate-100'}`
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

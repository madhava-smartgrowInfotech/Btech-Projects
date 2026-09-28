import { NavLink, useNavigate } from 'react-router-dom'
import { CalendarDays, LayoutDashboard, Leaf, LineChart, LogOut, NotebookPen, UserCog } from 'lucide-react'
import { useAuth } from '../auth'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/plan', label: 'Weekly plan', icon: CalendarDays },
  { to: '/log', label: 'Food log', icon: NotebookPen },
  { to: '/progress', label: 'Progress', icon: LineChart },
  { to: '/profile', label: 'Profile', icon: UserCog },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="mx-auto max-w-6xl px-4 h-14 flex items-center gap-4">
          <div className="flex items-center gap-2 font-semibold text-emerald-700"><Leaf className="h-5 w-5" /> NutriSense</div>
          <nav className="flex-1 flex gap-1 overflow-x-auto">
            {user?.has_profile && links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={({ isActive }) =>
                `flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${isActive ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon className="h-4 w-4" /><span className="hidden md:inline">{label}</span>
              </NavLink>
            ))}
          </nav>
          <span className="hidden sm:block text-sm text-slate-500">{user?.name}</span>
          <button className="btn-ghost !px-2.5" title="Log out" onClick={() => { logout(); nav('/') }}><LogOut className="h-4 w-4" /></button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  )
}

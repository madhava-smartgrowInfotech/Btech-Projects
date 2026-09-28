import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { Activity, BedDouble, BarChart3, LayoutDashboard, LogOut, Menu, Stethoscope, Workflow, X } from 'lucide-react'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/admissions', label: 'Admissions', icon: Stethoscope },
  { to: '/forecasts', label: 'Forecasts', icon: BedDouble },
  { to: '/allocation', label: 'Allocation', icon: Workflow },
  { to: '/performance', label: 'Model performance', icon: BarChart3 },
]

export default function Layout({ user, onLogout, children }) {
  const [open, setOpen] = useState(false)
  const nav = (
    <nav className="flex flex-col gap-1">
      {NAV.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          onClick={() => setOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
              isActive ? 'bg-teal-700 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`
          }
        >
          <Icon size={18} /> {label}
        </NavLink>
      ))}
    </nav>
  )
  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <aside className={`${open ? 'block' : 'hidden'} lg:block lg:w-60 bg-slate-900 p-4 lg:min-h-screen lg:sticky lg:top-0`}>
        <Link to="/" className="hidden lg:flex items-center gap-2 text-white font-semibold text-lg mb-8 px-2">
          <Activity className="text-teal-400" /> HospiSense
        </Link>
        {nav}
        <div className="mt-8 border-t border-slate-800 pt-4 px-2 text-xs text-slate-400">
          <div className="text-slate-200 text-sm">{user.name}</div>
          <div className="capitalize">{user.role}</div>
          <button onClick={onLogout} className="mt-3 flex items-center gap-2 text-slate-300 hover:text-white cursor-pointer">
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </aside>
      <div className="flex-1 min-w-0">
        <header className="lg:hidden flex items-center justify-between bg-slate-900 text-white px-4 py-3">
          <span className="flex items-center gap-2 font-semibold"><Activity className="text-teal-400" /> HospiSense</span>
          <button onClick={() => setOpen(!open)} aria-label="Menu">{open ? <X /> : <Menu />}</button>
        </header>
        <main className="p-4 lg:p-8 max-w-7xl mx-auto">{children}</main>
      </div>
    </div>
  )
}

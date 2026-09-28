import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, Droplets, FlaskConical, LineChart, LogOut, Map, Menu, ShieldAlert, X } from 'lucide-react'
import { useAuth } from '../auth.jsx'

const NAV = [
  { to: '/dashboard', label: 'Operations', icon: Activity },
  { to: '/quality', label: 'Water quality', icon: FlaskConical },
  { to: '/network', label: 'Network map', icon: Map },
  { to: '/forecast', label: 'Demand forecast', icon: LineChart },
  { to: '/leaks', label: 'Leaks & anomalies', icon: ShieldAlert },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen flex">
      {open && <div className="fixed inset-0 bg-slate-900/30 z-[1090] lg:hidden" onClick={() => setOpen(false)} />}
      <aside
        className={`fixed inset-y-0 left-0 z-[1100] w-60 bg-white border-r border-slate-200 p-4 flex flex-col transition-transform lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2 text-sky-700 font-semibold text-lg">
            <Droplets className="w-6 h-6" /> AquaVision
          </div>
          <button className="lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu">
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${isActive ? 'bg-sky-50 text-sky-700' : 'text-slate-600 hover:bg-slate-100'}`
              }
            >
              <Icon className="w-4 h-4" /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto border-t border-slate-200 pt-4">
          <div className="text-sm font-medium text-slate-800">{user?.name}</div>
          <div className="text-xs text-slate-500 capitalize">{user?.role}</div>
          <button
            className="mt-3 flex items-center gap-2 text-sm text-slate-600 hover:text-rose-600"
            onClick={() => {
              logout()
              nav('/login')
            }}
          >
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>
      </aside>
      <div className="flex-1 lg:ml-60 min-w-0">
        <header className="lg:hidden sticky top-0 z-[1000] bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
          <button onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="w-5 h-5" />
          </button>
          <span className="font-semibold text-sky-700">AquaVision</span>
        </header>
        <main className="p-4 md:p-8 max-w-7xl mx-auto">{children}</main>
      </div>
    </div>
  )
}

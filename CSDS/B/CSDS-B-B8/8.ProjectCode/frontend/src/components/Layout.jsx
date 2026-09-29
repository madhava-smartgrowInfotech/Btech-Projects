import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, Bell, BarChart3, CalendarDays, LogOut, Menu, Users } from 'lucide-react'
import Countdown from './Countdown.jsx'

const NAV = [
  { to: '/monitor', label: 'Live monitor', icon: Activity },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/contacts', label: 'Contacts & settings', icon: Users },
  { to: '/report', label: 'Daily report', icon: CalendarDays },
  { to: '/performance', label: 'Model performance', icon: BarChart3 },
]

export default function Layout({ children }) {
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const user = JSON.parse(localStorage.getItem('cw_user') || '{}')
  const logout = () => {
    localStorage.removeItem('cw_token')
    localStorage.removeItem('cw_user')
    nav('/login')
  }
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-4">
          <NavLink to="/monitor" className="flex items-center gap-2 font-semibold text-slate-900">
            <img src="/favicon.svg" className="w-7 h-7" alt="" /> CareWatch
          </NavLink>
          <nav className="hidden md:flex gap-1 ml-4">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm ${isActive ? 'bg-teal-50 text-teal-700 font-medium' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon className="w-4 h-4" /> {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto hidden md:flex items-center gap-3 text-sm text-slate-600">
            <span>{user.name}</span>
            <button onClick={logout} className="btn btn-secondary py-1.5"><LogOut className="w-4 h-4" /> Sign out</button>
          </div>
          <button className="md:hidden ml-auto" onClick={() => setOpen(!open)} aria-label="Menu"><Menu /></button>
        </div>
        {open && (
          <nav className="md:hidden border-t border-slate-200 px-4 py-2 flex flex-col">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)} className="flex items-center gap-2 py-2 text-slate-700">
                <Icon className="w-4 h-4" /> {label}
              </NavLink>
            ))}
            <button onClick={logout} className="flex items-center gap-2 py-2 text-slate-700"><LogOut className="w-4 h-4" /> Sign out</button>
          </nav>
        )}
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      <Countdown />
    </div>
  )
}

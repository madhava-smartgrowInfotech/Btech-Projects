import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Activity, LogOut, Menu, Plus, X } from 'lucide-react'
import { useAuth } from '../auth'

const LINKS = {
  patient: [
    ['/book', 'Book a visit'],
    ['/tokens', 'My tokens'],
    ['/referrals', 'Referrals'],
  ],
  staff: [
    ['/console', 'Hospital console'],
    ['/referrals', 'Referrals'],
  ],
  admin: [
    ['/dashboard', 'District dashboard'],
    ['/console', 'Hospital console'],
    ['/referrals', 'Referrals'],
  ],
}

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const links = user ? LINKS[user.role] : []
  const linkCls = ({ isActive }) =>
    `rounded-lg px-3 py-2 text-sm font-medium ${isActive ? 'bg-teal-50 text-teal-800' : 'text-slate-600 hover:bg-slate-100'}`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-[1000]">
        <div className="max-w-6xl mx-auto flex items-center gap-4 px-4 h-14">
          <Link to="/" className="flex items-center gap-2 font-bold text-teal-800">
            <span className="grid place-items-center h-8 w-8 rounded-lg bg-teal-700 text-white">
              <Plus className="h-5 w-5" strokeWidth={3} />
            </span>
            MediQueue
          </Link>
          <nav className="hidden md:flex items-center gap-1 ml-4">
            {links.map(([to, label]) => (
              <NavLink key={to} to={to} className={linkCls}>
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto hidden md:flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-slate-500">
                  {user.name} <span className="text-xs rounded bg-slate-100 px-1.5 py-0.5 ml-1">{user.role}</span>
                </span>
                <button
                  className="btn-outline !px-3"
                  onClick={() => {
                    logout()
                    nav('/login')
                  }}
                >
                  <LogOut className="h-4 w-4" /> Log out
                </button>
              </>
            ) : (
              <Link to="/login" className="btn-primary">
                Log in
              </Link>
            )}
          </div>
          <button className="md:hidden ml-auto p-2" onClick={() => setOpen(!open)} aria-label="Menu">
            {open ? <X /> : <Menu />}
          </button>
        </div>
        {open && (
          <div className="md:hidden border-t border-slate-200 px-4 py-2 flex flex-col gap-1" onClick={() => setOpen(false)}>
            {links.map(([to, label]) => (
              <NavLink key={to} to={to} className={linkCls}>
                {label}
              </NavLink>
            ))}
            {user ? (
              <button
                className="text-left rounded-lg px-3 py-2 text-sm text-slate-600"
                onClick={() => {
                  logout()
                  nav('/login')
                }}
              >
                Log out ({user.name})
              </button>
            ) : (
              <NavLink to="/login" className={linkCls}>
                Log in
              </NavLink>
            )}
          </div>
        )}
      </header>
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
      <footer className="text-center text-xs text-slate-400 py-4 flex items-center justify-center gap-1">
        <Activity className="h-3 w-3" /> MediQueue - decision support for outpatient care. Map data &copy; OpenStreetMap
        contributors.
      </footer>
    </div>
  )
}

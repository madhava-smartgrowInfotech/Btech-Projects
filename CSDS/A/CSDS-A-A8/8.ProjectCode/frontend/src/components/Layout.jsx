import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Activity, BarChart3, Brain, Dna, Fingerprint, LogOut, Menu, ScanEye } from 'lucide-react'
import { clearSession, getUser } from '../api.js'

const links = [
  { to: '/mri', label: 'MRI analysis', icon: Brain },
  { to: '/label-efficiency', label: 'Label efficiency', icon: BarChart3 },
  { to: '/dna', label: 'DNA analysis', icon: Dna },
  { to: '/str', label: 'STR matching', icon: Fingerprint },
  { to: '/performance', label: 'Model performance', icon: Activity },
]

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-white">
        <ScanEye size={18} />
      </span>
      BioSight
    </Link>
  )
}

export default function Layout({ children }) {
  const user = getUser()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const logout = () => {
    clearSession()
    nav('/login')
  }
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <Logo />
          <nav className="hidden gap-1 lg:flex">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to}
                className={({ isActive }) => `flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm ${isActive ? 'bg-teal-50 font-medium text-teal-700' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon size={16} /> {label}
              </NavLink>
            ))}
          </nav>
          <div className="hidden items-center gap-3 lg:flex">
            <span className="text-sm text-slate-500">{user?.name}</span>
            <button onClick={logout} className="btn-outline px-3 py-1.5"><LogOut size={15} /> Sign out</button>
          </div>
          <button className="lg:hidden" onClick={() => setOpen(!open)} aria-label="Menu"><Menu /></button>
        </div>
        {open && (
          <div className="border-t border-slate-200 px-4 py-2 lg:hidden">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)} className="flex items-center gap-2 py-2 text-sm text-slate-700">
                <Icon size={16} /> {label}
              </NavLink>
            ))}
            <button onClick={logout} className="flex items-center gap-2 py-2 text-sm text-slate-700"><LogOut size={16} /> Sign out</button>
          </div>
        )}
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  )
}

import { NavLink, useNavigate } from 'react-router-dom'
import { Building2, HeartPulse, LogOut, ScrollText, Stethoscope, UserRound } from 'lucide-react'
import { useAuth } from '../App.jsx'

const LINKS = {
  patient: [{ to: '/patient', label: 'My record', icon: UserRound }],
  doctor: [{ to: '/doctor', label: 'Patients', icon: Stethoscope }],
  staff: [{ to: '/hospital', label: 'Hospital console', icon: Building2 }],
  admin: [{ to: '/hospital', label: 'Hospitals & MPI', icon: Building2 }],
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const links = [...(LINKS[user.role] || []), { to: '/audit', label: 'Audit & consent log', icon: ScrollText }]
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center gap-4">
          <NavLink to="/" className="flex items-center gap-2 font-bold text-slate-900">
            <HeartPulse className="w-6 h-6 text-teal-600" /> UniHealth
          </NavLink>
          <nav className="flex flex-wrap gap-1">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to}
                className={({ isActive }) => `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm ${isActive ? 'bg-teal-50 text-teal-800 font-medium' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon className="w-4 h-4" /> {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <div className="text-right leading-tight">
              <div className="font-medium text-slate-800">{user.display_name}</div>
              <div className="text-xs text-slate-500 capitalize">{user.role}{user.role !== 'patient' && user.hospital_name ? ` - ${user.hospital_name}` : ''}</div>
            </div>
            <button onClick={() => { logout(); nav('/login') }} className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-slate-600 hover:bg-slate-100" title="Sign out">
              <LogOut className="w-4 h-4" /> <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">{children}</main>
    </div>
  )
}

import { BarChart3, LayoutDashboard, LogOut, Menu, Network, ShieldCheck, Users, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../App'

const NAV = [
  { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/app/taxpayers', label: 'Taxpayers', icon: Users },
  { to: '/app/graph', label: 'Fraud rings', icon: Network },
  { to: '/app/performance', label: 'Model performance', icon: BarChart3 },
]

export function Logo({ light = false }) {
  return (
    <div className="flex items-center gap-2">
      <div className="p-1.5 rounded-lg bg-indigo-600 text-white"><ShieldCheck size={18} /></div>
      <span className={`font-semibold tracking-tight ${light ? 'text-white' : 'text-slate-900'}`}>TaxSentinel</span>
    </div>
  )
}

export default function Layout() {
  const { user, signOut } = useAuth()
  const [open, setOpen] = useState(false)
  const nav = (
    <nav className="flex flex-col gap-1">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm ${isActive ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-100'}`}>
          <Icon size={17} /> {label}
        </NavLink>
      ))}
    </nav>
  )
  return (
    <div className="min-h-screen lg:flex">
      <aside className="hidden lg:flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white p-4 sticky top-0 h-screen">
        <div className="mb-6 px-1"><Logo /></div>
        {nav}
        <div className="mt-auto border-t border-slate-100 pt-3">
          <div className="px-1 text-sm font-medium text-slate-800 truncate">{user?.name}</div>
          <div className="px-1 text-xs text-slate-500 truncate">{user?.email}</div>
          <button onClick={signOut} className="mt-2 flex items-center gap-2 px-1 text-sm text-slate-600 hover:text-red-600">
            <LogOut size={15} /> Sign out
          </button>
        </div>
      </aside>
      <header className="lg:hidden flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 sticky top-0 z-20">
        <Logo />
        <button onClick={() => setOpen(!open)} aria-label="Menu">{open ? <X /> : <Menu />}</button>
      </header>
      {open && (
        <div className="lg:hidden border-b border-slate-200 bg-white p-3 sticky top-[57px] z-20">
          {nav}
          <button onClick={signOut} className="mt-2 flex items-center gap-2 px-3 text-sm text-slate-600"><LogOut size={15} /> Sign out</button>
        </div>
      )}
      <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 max-w-[1400px]">
        <Outlet />
      </main>
    </div>
  )
}

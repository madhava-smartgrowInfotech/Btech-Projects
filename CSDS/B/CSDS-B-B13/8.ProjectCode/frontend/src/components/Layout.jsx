import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ShieldCheck, LogOut } from 'lucide-react'
import { useAuth } from '../auth'

export default function Layout({ children }) {
  const { email, logout } = useAuth()
  const navigate = useNavigate()
  const link = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium ${
      isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'}`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-2">
          <Link to="/app/targets" className="flex items-center gap-2 font-extrabold text-lg">
            <ShieldCheck className="text-brand-500" /> APISentry
          </Link>
          <nav className="flex items-center gap-1 ml-6">
            <NavLink to="/app/targets" className={link}>Targets</NavLink>
            <NavLink to="/app/scans" className={link}>Scans</NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-sm text-slate-500 hidden sm:block">{email}</span>
            <button onClick={() => { logout(); navigate('/') }}
              className="btn-ghost !py-1.5 text-sm">
              <LogOut size={16} /> Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">{children}</main>
      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        APISentry · automated OWASP API Top 10 security testing · scans localhost targets only
      </footer>
    </div>
  )
}

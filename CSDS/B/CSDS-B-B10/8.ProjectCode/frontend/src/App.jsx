import { useState } from 'react'
import { Link, Navigate, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { Gauge, ImageIcon, LockKeyhole, LogOut, Radio, ShieldCheck } from 'lucide-react'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Studio from './pages/Studio'
import Lab from './pages/Lab'
import Live from './pages/Live'
import Benchmark from './pages/Benchmark'

function getUser() {
  try { return JSON.parse(localStorage.getItem('sc_user')) } catch { return null }
}

function Protected({ user, children }) {
  return user && localStorage.getItem('sc_token') ? children : <Navigate to="/login" replace />
}

function Shell({ user, onLogout, children }) {
  const nav = [
    ['/studio', 'Image studio', ImageIcon],
    ['/lab', 'Security lab', ShieldCheck],
    ['/live', 'Live link', Radio],
    ['/benchmark', 'Benchmark', Gauge],
  ]
  return (
    <div className="min-h-screen">
      <header className="bg-slate-900 text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3">
          <Link to="/studio" className="flex items-center gap-2 font-semibold">
            <LockKeyhole className="h-5 w-5 text-sky-400" /> SkyCipher
          </Link>
          <nav className="flex flex-1 flex-wrap gap-1">
            {nav.map(([to, label, Icon]) => (
              <NavLink key={to} to={to} className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm ${isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'}`}>
                <Icon className="h-4 w-4" /> {label}
              </NavLink>
            ))}
          </nav>
          <span className="text-sm text-slate-300">{user?.name}</span>
          <button onClick={onLogout} className="flex items-center gap-1 text-sm text-slate-300 hover:text-white">
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(getUser())
  const navigate = useNavigate()
  const onAuth = (data) => {
    localStorage.setItem('sc_token', data.token)
    localStorage.setItem('sc_user', JSON.stringify(data.user))
    setUser(data.user)
    navigate('/studio')
  }
  const logout = () => {
    localStorage.removeItem('sc_token')
    localStorage.removeItem('sc_user')
    setUser(null)
    navigate('/')
  }
  const page = (el) => <Protected user={user}><Shell user={user} onLogout={logout}>{el}</Shell></Protected>
  return (
    <Routes>
      <Route path="/" element={<Landing user={user} />} />
      <Route path="/login" element={<Login onAuth={onAuth} />} />
      <Route path="/studio" element={page(<Studio />)} />
      <Route path="/lab" element={page(<Lab />)} />
      <Route path="/live" element={page(<Live />)} />
      <Route path="/benchmark" element={page(<Benchmark />)} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

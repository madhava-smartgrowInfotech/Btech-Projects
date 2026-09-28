import { Suspense, createContext, lazy, useContext, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import {
  BarChart3, Briefcase, Code2, FileText, GraduationCap, LayoutDashboard, LogOut, Menu, MessageSquare, Trophy, UserCheck,
} from 'lucide-react'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Practice from './pages/Practice'
import Problems from './pages/Problems'
const ProblemEditor = lazy(() => import('./pages/ProblemEditor'))
import Contests from './pages/Contests'
import ContestDetail from './pages/ContestDetail'
import Interview from './pages/Interview'
import Expert from './pages/Expert'
import ResumePage from './pages/Resume'
import Recruiter from './pages/Recruiter'
import DriveDetail from './pages/DriveDetail'
import Analytics from './pages/Analytics'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)

export const HOME = { candidate: '/dashboard', recruiter: '/recruiter', career: '/analytics', expert: '/expert' }

const NAV = {
  candidate: [
    ['/dashboard', 'Dashboard', LayoutDashboard],
    ['/practice', 'Aptitude & MCQs', GraduationCap],
    ['/problems', 'Coding', Code2],
    ['/contests', 'Contests', Trophy],
    ['/interview', 'Mock interview', MessageSquare],
    ['/resume', 'Resume', FileText],
  ],
  recruiter: [
    ['/recruiter', 'Drives', Briefcase],
    ['/analytics', 'Readiness', BarChart3],
    ['/contests', 'Leaderboards', Trophy],
  ],
  career: [
    ['/analytics', 'Readiness analytics', BarChart3],
    ['/contests', 'Contests', Trophy],
  ],
  expert: [
    ['/expert', 'Interview queue', UserCheck],
    ['/contests', 'Leaderboards', Trophy],
  ],
}

const ROLE_LABEL = { candidate: 'Candidate', recruiter: 'Recruiter', career: 'Career services', expert: 'Expert interviewer' }

function Shell({ children }) {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const items = NAV[user.role] || []
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-4">
          <NavLink to={HOME[user.role]} className="flex items-center gap-2 font-bold text-slate-900 shrink-0">
            <span className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-sm">T</span>
            TalentTrack
          </NavLink>
          <nav className="hidden md:flex items-center gap-1 flex-1 overflow-x-auto">
            {items.map(([to, label, Icon]) => (
              <NavLink key={to} to={to}
                className={({ isActive }) => `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm whitespace-nowrap ${isActive ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon className="w-4 h-4" /> {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto hidden md:flex items-center gap-3">
            <div className="text-right leading-tight">
              <div className="text-sm font-medium text-slate-800">{user.name}</div>
              <div className="text-xs text-slate-500">{ROLE_LABEL[user.role]}</div>
            </div>
            <button className="btn-secondary !px-2.5" onClick={logout} title="Sign out"><LogOut className="w-4 h-4" /></button>
          </div>
          <button className="md:hidden ml-auto btn-secondary !px-2.5" onClick={() => setOpen(!open)}><Menu className="w-4 h-4" /></button>
        </div>
        {open && (
          <div className="md:hidden border-t border-slate-200 px-4 py-2 space-y-1 bg-white">
            {items.map(([to, label, Icon]) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)} className="flex items-center gap-2 px-2 py-2 rounded text-sm text-slate-700">
                <Icon className="w-4 h-4" /> {label}
              </NavLink>
            ))}
            <button className="flex items-center gap-2 px-2 py-2 text-sm text-slate-700" onClick={logout}><LogOut className="w-4 h-4" /> Sign out</button>
          </div>
        )}
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6"><Suspense fallback={<div className="text-sm text-slate-500 py-6 text-center">Loading...</div>}>{children}</Suspense></main>
    </div>
  )
}

function Guard({ roles, children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to={HOME[user.role]} replace />
  return <Shell>{children}</Shell>
}

export default function App() {
  const nav = useNavigate()
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('tt_user') || 'null')
    } catch {
      return null
    }
  })
  const login = (token, u) => {
    localStorage.setItem('tt_token', token)
    localStorage.setItem('tt_user', JSON.stringify(u))
    setUser(u)
    nav(HOME[u.role] || '/')
  }
  const logout = () => {
    localStorage.removeItem('tt_token')
    localStorage.removeItem('tt_user')
    setUser(null)
    nav('/login')
  }
  const C = ['candidate']
  return (
    <AuthCtx.Provider value={{ user, login, logout }}>
      <Routes>
        <Route path="/" element={user ? <Navigate to={HOME[user.role]} replace /> : <Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Guard roles={C}><Dashboard /></Guard>} />
        <Route path="/practice" element={<Guard roles={C}><Practice /></Guard>} />
        <Route path="/problems" element={<Guard roles={C}><Problems /></Guard>} />
        <Route path="/problems/:slug" element={<Guard roles={C}><ProblemEditor /></Guard>} />
        <Route path="/contests" element={<Guard><Contests /></Guard>} />
        <Route path="/contests/:id" element={<Guard><ContestDetail /></Guard>} />
        <Route path="/interview" element={<Guard roles={C}><Interview /></Guard>} />
        <Route path="/interview/:id" element={<Guard roles={C}><Interview /></Guard>} />
        <Route path="/resume" element={<Guard roles={C}><ResumePage /></Guard>} />
        <Route path="/expert" element={<Guard roles={['expert']}><Expert /></Guard>} />
        <Route path="/recruiter" element={<Guard roles={['recruiter']}><Recruiter /></Guard>} />
        <Route path="/recruiter/drives/:id" element={<Guard roles={['recruiter']}><DriveDetail /></Guard>} />
        <Route path="/analytics" element={<Guard roles={['career', 'recruiter']}><Analytics /></Guard>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthCtx.Provider>
  )
}

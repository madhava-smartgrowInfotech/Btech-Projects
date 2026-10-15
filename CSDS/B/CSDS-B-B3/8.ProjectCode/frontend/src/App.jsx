import { Suspense, lazy, useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell, homeFor } from './components/ui/layout'
import { RequireAuth, useAuth } from './lib/auth'
import { Skeleton } from './components/ui'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Learning = lazy(() => import('./pages/Learning'))
const Graph = lazy(() => import('./pages/Graph'))
const Career = lazy(() => import('./pages/Career'))
const Marketplace = lazy(() => import('./pages/Marketplace'))
const Mentors = lazy(() => import('./pages/Mentors'))
const Interview = lazy(() => import('./pages/Interview'))
const Coding = lazy(() => import('./pages/Coding'))
const Progress = lazy(() => import('./pages/Progress'))
const Research = lazy(() => import('./pages/Research'))
const Profile = lazy(() => import('./pages/Profile'))
const MentorPanel = lazy(() => import('./pages/MentorPanel'))
const Admin = lazy(() => import('./pages/Admin'))

function Fallback() {
  return (
    <div className="container" style={{ paddingTop: 40 }} aria-busy="true" aria-label="Loading">
      <Skeleton height={30} width={260} />
      <Skeleton height={180} style={{ marginTop: 24 }} />
    </div>
  )
}

function ScrollTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

const guard = (roles, el) => <RequireAuth roles={roles}>{el}</RequireAuth>
const S = ['student']

export default function App() {
  const { user } = useAuth()
  const home = homeFor(user?.role)
  return (
    <Suspense fallback={<Fallback />}>
      <ScrollTop />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={user ? <Navigate to={home} replace /> : <Login />} />
        <Route path="/app" element={guard(null, <AppShell />)}>
          <Route index element={<Navigate to={home} replace />} />
          <Route path="dashboard" element={guard(S, <Dashboard />)} />
          <Route path="learning" element={guard(S, <Learning />)} />
          <Route path="graph" element={guard(S, <Graph />)} />
          <Route path="career" element={guard(S, <Career />)} />
          <Route path="marketplace" element={guard(['student', 'mentor'], <Marketplace />)} />
          <Route path="mentors" element={guard(S, <Mentors />)} />
          <Route path="interview" element={guard(S, <Interview />)} />
          <Route path="coding" element={guard(S, <Coding />)} />
          <Route path="progress" element={guard(S, <Progress />)} />
          <Route path="research" element={<Research />} />
          <Route path="profile" element={guard(['student', 'mentor'], <Profile />)} />
          <Route path="mentor-panel" element={guard(['mentor'], <MentorPanel />)} />
          <Route path="admin" element={guard(['admin'], <Admin />)} />
          <Route path="*" element={<Navigate to={home} replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

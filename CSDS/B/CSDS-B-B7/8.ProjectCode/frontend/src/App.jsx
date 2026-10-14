import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './lib/auth'
import { AppShell } from './components/ui/Layout'
import { SkeletonBlock } from './components/ui/Feedback'
import { PageTransition } from './components/motion'

// Every screen is its own chunk, so the landing page and sign-in load without the charts.
const Landing = lazy(() => import('./pages/Landing.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const Admissions = lazy(() => import('./pages/Admissions.jsx'))
const Forecasts = lazy(() => import('./pages/Forecasts.jsx'))
const Allocation = lazy(() => import('./pages/Allocation.jsx'))
const Performance = lazy(() => import('./pages/Performance.jsx'))

/** Signed-in screens: redirect to sign-in when there is no session, otherwise render inside the app shell. */
function Protected() {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user) return <Navigate to="/login" replace />
  return (
    <AppShell>
      <PageTransition key={loc.pathname}>
        <Suspense fallback={<SkeletonBlock label="Loading page" rows={5} />}>
          <Outlet />
        </Suspense>
      </PageTransition>
    </AppShell>
  )
}

export default function App() {
  const { user } = useAuth()
  return (
    <Suspense fallback={<SkeletonBlock label="Loading page" rows={5} />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
        <Route element={<Protected />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admissions" element={<Admissions />} />
          <Route path="/forecasts" element={<Forecasts />} />
          <Route path="/allocation" element={<Allocation />} />
          <Route path="/performance" element={<Performance />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

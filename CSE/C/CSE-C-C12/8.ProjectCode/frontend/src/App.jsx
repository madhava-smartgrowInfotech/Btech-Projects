import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell, PublicShell, SkeletonBlock } from './components/ui'
import { PageTransition } from './components/motion'
import { useAuth } from './lib/auth'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Assistant = lazy(() => import('./pages/Assistant'))
const History = lazy(() => import('./pages/History'))
const ConsultationDetail = lazy(() => import('./pages/ConsultationDetail'))
const About = lazy(() => import('./pages/About'))
const NotFound = lazy(() => import('./pages/NotFound'))

function Loading() {
  return (
    <div className="container" style={{ padding: '48px 16px' }}>
      <SkeletonBlock rows={4} label="Loading page" />
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

/** Signed-in routes render inside the sidebar shell; others bounce to /login and come back after. */
function Private({ children }) {
  const { user, ready } = useAuth()
  const loc = useLocation()
  if (!ready) return <Loading />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return (
    <AppShell>
      <PageTransition>{children}</PageTransition>
    </AppShell>
  )
}

/** Login / register skip the form when a session already exists. */
function GuestOnly({ children }) {
  const { user, ready } = useAuth()
  if (!ready) return <Loading />
  if (user) return <Navigate to="/assistant" replace />
  return <PublicShell>{children}</PublicShell>
}

/** About is reachable signed in (sidebar) or signed out (public header). */
function Either({ children }) {
  const { user, ready } = useAuth()
  if (!ready) return <Loading />
  const Shell = user ? AppShell : PublicShell
  return (
    <Shell>
      <PageTransition>{children}</PageTransition>
    </Shell>
  )
}

export default function App() {
  return (
    <>
      <ScrollTop />
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/" element={<PublicShell><Landing /></PublicShell>} />
          <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
          <Route path="/register" element={<GuestOnly><Register /></GuestOnly>} />
          <Route path="/assistant" element={<Private><Assistant /></Private>} />
          <Route path="/history" element={<Private><History /></Private>} />
          <Route path="/history/:id" element={<Private><ConsultationDetail /></Private>} />
          <Route path="/about" element={<Either><About /></Either>} />
          <Route path="*" element={<PublicShell><NotFound /></PublicShell>} />
        </Routes>
      </Suspense>
    </>
  )
}

import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell, PublicShell, SkeletonBlock } from './components/ui'
import { PageTransition } from './components/motion'
import { useAuth } from './lib/auth'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Detect = lazy(() => import('./pages/Detect'))
const Result = lazy(() => import('./pages/Result'))
const History = lazy(() => import('./pages/History'))
const About = lazy(() => import('./pages/About'))
const NotFound = lazy(() => import('./pages/NotFound'))

const Loading = () => (
  <div className="container" style={{ padding: '48px 16px' }}>
    <SkeletonBlock rows={4} label="Loading page" />
  </div>
)

/** Signed-in area. Unauthenticated visitors are sent to /login and returned afterwards. */
function Private({ children }) {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <Loading />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return <AppShell>{children}</AppShell>
}

function Public({ children }) {
  return <PublicShell>{children}</PublicShell>
}

/** Scroll to the top on navigation, or to the #anchor when there is one. */
function ScrollManager() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (hash) {
      const el = document.getElementById(hash.slice(1))
      if (el) {
        el.scrollIntoView()
        return
      }
    }
    window.scrollTo(0, 0)
  }, [pathname, hash])
  return null
}

export default function App() {
  const loc = useLocation()
  return (
    <>
      <ScrollManager />
      <Suspense fallback={<Loading />}>
        <Routes location={loc}>
          <Route path="/" element={<Public><Landing /></Public>} />
          <Route path="/login" element={<Public><PageTransition><Login /></PageTransition></Public>} />
          <Route path="/app" element={<Private><PageTransition><Dashboard /></PageTransition></Private>} />
          <Route path="/app/detect" element={<Private><PageTransition><Detect /></PageTransition></Private>} />
          <Route path="/app/result/:id" element={<Private><PageTransition><Result /></PageTransition></Private>} />
          <Route path="/app/history" element={<Private><PageTransition><History /></PageTransition></Private>} />
          <Route path="/app/about" element={<Private><PageTransition><About /></PageTransition></Private>} />
          <Route path="*" element={<Public><NotFound /></Public>} />
        </Routes>
      </Suspense>
    </>
  )
}

import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Phone } from 'lucide-react'
import { AppShell, PublicShell, SkeletonBlock, Container, Button } from './components/ui'
import { AlertOverlays } from './features/AlertOverlays'
import { useAuth } from './lib/auth'
import { useMonitor } from './state/MonitorContext'

const Landing = lazy(() => import('./pages/Landing'))
const Monitor = lazy(() => import('./pages/Monitor'))
const Manual = lazy(() => import('./pages/Manual'))
const Response = lazy(() => import('./pages/Response'))
const NotFound = lazy(() => import('./pages/NotFound'))
const Auth = lazy(() => import('./pages/Auth'))

function Loading() {
  return (
    <Container style={{ padding: '48px 16px' }}>
      <SkeletonBlock rows={4} label="Loading page" />
    </Container>
  )
}

/** Sends signed-out visitors to /login and brings them back to the page they asked for. */
function RequireAuth({ children }) {
  const { status, leftOnPurpose } = useAuth()
  const loc = useLocation()
  if (status === 'loading') return <Loading />
  if (status === 'out' && leftOnPurpose) return <Navigate to="/" replace />
  if (status === 'out') return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}

function ScrollTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function SidebarFooter() {
  return (
    <div className="card card-flat" style={{ padding: 12 }}>
      <strong style={{ display: 'block' }}>In a real emergency</strong>
      <span className="tiny muted">Call 108 (ambulance) or 112. This demo sends nothing to real responders.</span>
      <div className="row" style={{ marginTop: 8 }}>
        <Button size="sm" icon={Phone} href="tel:108">108</Button>
        <Button size="sm" icon={Phone} href="tel:112">112</Button>
      </div>
    </div>
  )
}

export default function App() {
  const { health } = useMonitor()
  const shell = (page) => (
    <RequireAuth>
      <AppShell health={health} footer={<SidebarFooter />}>
        <Suspense fallback={<SkeletonBlock rows={5} label="Loading page" />}>{page}</Suspense>
      </AppShell>
    </RequireAuth>
  )
  const pub = (page) => (
    <PublicShell health={health}>
      <Suspense fallback={<Loading />}>{page}</Suspense>
    </PublicShell>
  )
  return (
    <>
      <ScrollTop />
      <Routes>
        <Route
          path="/"
          element={
            <PublicShell health={health}>
              <Suspense fallback={<Loading />}>
                <Landing />
              </Suspense>
            </PublicShell>
          }
        />
        <Route path="/login" element={pub(<Auth key="login" mode="login" />)} />
        <Route path="/register" element={pub(<Auth key="register" mode="register" />)} />
        <Route path="/monitor" element={shell(<Monitor />)} />
        <Route path="/manual" element={shell(<Manual />)} />
        <Route path="/response" element={shell(<Response />)} />
        <Route
          path="*"
          element={
            <PublicShell health={health}>
              <Suspense fallback={<Loading />}>
                <NotFound />
              </Suspense>
            </PublicShell>
          }
        />
      </Routes>
      <AlertOverlays />
    </>
  )
}

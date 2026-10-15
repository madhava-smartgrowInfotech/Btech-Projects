import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './lib/auth'
import { AppShell, PublicShell, SkeletonBlock, Container } from './components/ui'
import { PageTransition, SmoothScroll } from './components/motion'

const Landing = lazy(() => import('./pages/Landing.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const Calls = lazy(() => import('./pages/Calls.jsx'))
const CallDetail = lazy(() => import('./pages/CallDetail.jsx'))
const Studio = lazy(() => import('./pages/Studio.jsx'))
const Analytics = lazy(() => import('./pages/Analytics.jsx'))
const Performance = lazy(() => import('./pages/Performance.jsx'))

function Loading() {
  return (
    <Container style={{ padding: '48px 16px' }}>
      <SkeletonBlock rows={5} label="Loading page" />
    </Container>
  )
}

function RequireAuth() {
  const { user, signedOut } = useAuth()
  const loc = useLocation()
  if (!user) return <Navigate to={signedOut ? '/' : '/login'} replace />
  return (
    <AppShell>
      <Suspense fallback={<Loading />}>
        <PageTransition key={loc.pathname}>
          <Outlet />
        </PageTransition>
      </Suspense>
    </AppShell>
  )
}

function Public({ children, smooth }) {
  const body = (
    <PublicShell>
      <Suspense fallback={<Loading />}>{children}</Suspense>
    </PublicShell>
  )
  return smooth ? <SmoothScroll>{body}</SmoothScroll> : body
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Public smooth><Landing /></Public>} />
      <Route path="/login" element={<Public><Login /></Public>} />
      <Route element={<RequireAuth />}>
        <Route path="/calls" element={<Calls />} />
        <Route path="/calls/:id" element={<CallDetail />} />
        <Route path="/studio" element={<Studio />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/performance" element={<Performance />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

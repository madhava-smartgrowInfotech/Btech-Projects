import Lenis from 'lenis'
import { lazy, Suspense, useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import AppShell from './components/ui/AppShell'
import { PageSkeleton } from './components/ui/feedback'
import { prefersReducedMotion } from './lib/reduced'

const Landing = lazy(() => import('./pages/Landing'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const SecureTransfer = lazy(() => import('./pages/SecureTransfer'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Performance = lazy(() => import('./pages/Performance'))
const NotFound = lazy(() => import('./pages/NotFound'))

// Smooth scrolling on the landing page only (never with reduced motion); the app screens scroll natively.
function useLandingScroll() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
    if (pathname !== '/' || prefersReducedMotion()) return
    const lenis = new Lenis({ lerp: 0.12 })
    let raf
    const loop = (t) => { lenis.raf(t); raf = requestAnimationFrame(loop) }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); lenis.destroy() }
  }, [pathname])
}

export default function App() {
  useLandingScroll()
  return (
    <Suspense fallback={<div className="p-6"><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="secure" element={<SecureTransfer />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="performance" element={<Performance />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  )
}

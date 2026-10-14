import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import { ThemeProvider } from './lib/theme'
import { StatsProvider } from './lib/stats'
import { AppShell, Skeleton, ToastProvider } from './components/ui'

// route-level code splitting
const Landing = lazy(() => import('./pages/Landing'))
const CheckUrl = lazy(() => import('./pages/CheckUrl'))
const Report = lazy(() => import('./pages/Report'))
const Intel = lazy(() => import('./pages/Intel'))
const Models = lazy(() => import('./pages/Models'))
const ActivityPage = lazy(() => import('./pages/Activity'))
const NotFound = lazy(() => import('./pages/NotFound'))

function PageSkeleton() {
  return (
    <div className="container" aria-busy="true" aria-label="Loading page">
      <Skeleton width={180} height={14} />
      <Skeleton width="45%" height={34} style={{ margin: '14px 0 28px' }} />
      <div className="grid grid-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={128} radius={12} />
        ))}
      </div>
      <Skeleton height={320} radius={12} style={{ marginTop: 18 }} />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <MotionConfig reducedMotion="user">
        <ToastProvider>
          <StatsProvider>
            <div className="grain" aria-hidden="true" />
            <Suspense fallback={<PageSkeleton />}>
              <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/app" element={<AppShell />}>
                  <Route index element={<Navigate to="check" replace />} />
                  <Route path="check" element={<Suspense fallback={<PageSkeleton />}><CheckUrl /></Suspense>} />
                  <Route path="report" element={<Suspense fallback={<PageSkeleton />}><Report /></Suspense>} />
                  <Route path="intel" element={<Suspense fallback={<PageSkeleton />}><Intel /></Suspense>} />
                  <Route path="models" element={<Suspense fallback={<PageSkeleton />}><Models /></Suspense>} />
                  <Route path="activity" element={<Suspense fallback={<PageSkeleton />}><ActivityPage /></Suspense>} />
                  <Route path="*" element={<Suspense fallback={<PageSkeleton />}><NotFound /></Suspense>} />
                </Route>
                <Route path="*" element={<NotFound standalone />} />
              </Routes>
            </Suspense>
          </StatsProvider>
        </ToastProvider>
      </MotionConfig>
    </ThemeProvider>
  )
}

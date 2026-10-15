import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import { ThemeProvider } from './lib/theme'
import { AuthProvider, useAuth } from './lib/auth'
import { HealthProvider } from './lib/health'
import { AppShell, ToastProvider } from './components/ui'
import { PageSkeleton } from './components/bio'

// route-level code splitting
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Mri = lazy(() => import('./pages/Mri'))
const LabelEfficiency = lazy(() => import('./pages/LabelEfficiency'))
const Dna = lazy(() => import('./pages/Dna'))
const StrMatch = lazy(() => import('./pages/StrMatch'))
const Performance = lazy(() => import('./pages/Performance'))
const History = lazy(() => import('./pages/History'))
const NotFound = lazy(() => import('./pages/NotFound'))

function RequireAuth({ children }) {
  const { user } = useAuth()
  const loc = useLocation()
  return user ? children : <Navigate to="/login" replace state={{ from: loc.pathname }} />
}

const page = (el) => <Suspense fallback={<PageSkeleton />}>{el}</Suspense>

export default function App() {
  return (
    <ThemeProvider>
      <MotionConfig reducedMotion="user">
        <ToastProvider>
          <AuthProvider>
            <HealthProvider>
              <div className="grain" aria-hidden="true" />
              <Suspense fallback={<PageSkeleton />}>
                <Routes>
                  <Route path="/" element={<Landing />} />
                  <Route path="/login" element={<Login />} />
                  <Route
                    path="/app"
                    element={
                      <RequireAuth>
                        <AppShell />
                      </RequireAuth>
                    }
                  >
                    <Route index element={<Navigate to="mri" replace />} />
                    <Route path="mri" element={page(<Mri />)} />
                    <Route path="label-efficiency" element={page(<LabelEfficiency />)} />
                    <Route path="dna" element={page(<Dna />)} />
                    <Route path="str" element={page(<StrMatch />)} />
                    <Route path="performance" element={page(<Performance />)} />
                    <Route path="history" element={page(<History />)} />
                    <Route path="*" element={page(<NotFound />)} />
                  </Route>
                  <Route path="*" element={<NotFound standalone />} />
                </Routes>
              </Suspense>
            </HealthProvider>
          </AuthProvider>
        </ToastProvider>
      </MotionConfig>
    </ThemeProvider>
  )
}

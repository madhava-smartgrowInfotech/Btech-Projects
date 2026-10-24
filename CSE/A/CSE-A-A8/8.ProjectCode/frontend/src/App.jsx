import { Suspense, lazy } from 'react'
import { Route, Routes } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import { ThemeProvider } from './lib/theme'
import { AuthProvider, RequireAuth } from './lib/auth'
import { AppShell, ToastProvider } from './components/ui'
import { PageSkeleton } from './components/lab'

// route-level code splitting
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Upload = lazy(() => import('./pages/Upload'))
const Analysis = lazy(() => import('./pages/Analysis'))
const Reports = lazy(() => import('./pages/Reports'))
const Trends = lazy(() => import('./pages/Trends'))
const Compare = lazy(() => import('./pages/Compare'))
const Insights = lazy(() => import('./pages/Insights'))
const About = lazy(() => import('./pages/About'))
const NotFound = lazy(() => import('./pages/NotFound'))

const page = (el) => <Suspense fallback={<PageSkeleton />}>{el}</Suspense>

export default function App() {
  return (
    <ThemeProvider>
      <MotionConfig reducedMotion="user">
        <ToastProvider>
          <AuthProvider>
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
                  <Route index element={page(<Dashboard />)} />
                  <Route path="upload" element={page(<Upload />)} />
                  <Route path="analysis" element={page(<Analysis />)} />
                  <Route path="analysis/:id" element={page(<Analysis />)} />
                  <Route path="reports" element={page(<Reports />)} />
                  <Route path="trends" element={page(<Trends />)} />
                  <Route path="compare" element={page(<Compare />)} />
                  <Route path="insights" element={page(<Insights />)} />
                  <Route path="about" element={page(<About />)} />
                  <Route path="*" element={page(<NotFound />)} />
                </Route>
                <Route path="*" element={<NotFound standalone />} />
              </Routes>
            </Suspense>
          </AuthProvider>
        </ToastProvider>
      </MotionConfig>
    </ThemeProvider>
  )
}

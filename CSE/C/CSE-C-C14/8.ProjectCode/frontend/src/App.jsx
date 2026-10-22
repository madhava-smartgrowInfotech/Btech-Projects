import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell, PageSkeleton } from './components/ui'
import { useAuth } from './lib/auth'
import ErrorBoundary from './components/ErrorBoundary'

// Every screen is lazy-loaded so the landing page stays light.
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Analyze = lazy(() => import('./pages/Analyze'))
const Insights = lazy(() => import('./pages/Insights'))
const Models = lazy(() => import('./pages/Models'))
const Status = lazy(() => import('./pages/Status'))
const NotFound = lazy(() => import('./pages/NotFound'))

function RequireAuth({ children }) {
  const { user, checking } = useAuth()
  const loc = useLocation()
  if (checking) return <div className="container" style={{ paddingTop: 40 }}><PageSkeleton kpis={2} blocks={1} /></div>
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}

export default function App() {
  return (
    <ErrorBoundary>
    <Suspense fallback={<div className="container" style={{ paddingTop: 40 }}><PageSkeleton kpis={3} blocks={2} /></div>}>
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
          <Route index element={<Analyze />} />
          <Route path="insights" element={<Insights />} />
          <Route path="models" element={<Models />} />
          <Route path="status" element={<Status />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
    </ErrorBoundary>
  )
}

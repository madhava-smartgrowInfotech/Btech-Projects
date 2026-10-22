import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { PageSkeleton } from './components/ui/feedback'
import { useAuth } from './lib/auth'

// Route-level code splitting: every screen is its own chunk.
const AppShell = lazy(() => import('./components/ui/AppShell'))
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analyze = lazy(() => import('./pages/Analyze'))
const Performance = lazy(() => import('./pages/Performance'))
const Insights = lazy(() => import('./pages/Insights'))

function Guard({ children }) {
  const { user } = useAuth()
  const location = useLocation()
  return user ? children : <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
}

function Fallback() {
  return <div className="mx-auto max-w-5xl p-6"><PageSkeleton /></div>
}

export default function App() {
  const { user } = useAuth()
  return (
    <Suspense fallback={<Fallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={user ? <Navigate to="/app" replace /> : <Login />} />
        <Route path="/app" element={<Guard><AppShell /></Guard>}>
          <Route index element={<Dashboard />} />
          <Route path="analyze" element={<Analyze />} />
          <Route path="performance" element={<Performance />} />
          <Route path="insights" element={<Insights />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

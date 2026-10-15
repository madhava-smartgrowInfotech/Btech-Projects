import { lazy } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import AppShell from './components/ui/AppShell'
import { Suspense } from 'react'
import { PageSkeleton } from './components/ui/feedback'
import { useAuth } from './lib/auth'
import { HealthProvider } from './lib/health'

const Landing = lazy(() => import('./pages/Landing'))
const Auth = lazy(() => import('./pages/Auth'))
const Conversation = lazy(() => import('./pages/Conversation'))
const Practice = lazy(() => import('./pages/Practice'))
const History = lazy(() => import('./pages/History'))
const Performance = lazy(() => import('./pages/Performance'))

function Private() {
  const { user } = useAuth()
  const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return <HealthProvider><AppShell /></HealthProvider>
}

export default function App() {
  return (
    <Suspense fallback={<div className="p-8"><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Auth mode="login" />} />
        <Route path="/register" element={<Auth mode="register" />} />
        <Route path="/app" element={<Private />}>
          <Route index element={<Conversation />} />
          <Route path="practice" element={<Practice />} />
          <Route path="history" element={<History />} />
          <Route path="performance" element={<Performance />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

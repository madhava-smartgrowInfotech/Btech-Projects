import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { PageSkeleton } from './components/ui/feedback'
import { useAuth } from './lib/auth'

// Route-level code splitting: every screen is its own chunk.
const AppShell = lazy(() => import('./components/ui/AppShell'))
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Overview = lazy(() => import('./pages/Overview'))
const Taxpayers = lazy(() => import('./pages/Taxpayers'))
const TaxpayerProfile = lazy(() => import('./pages/TaxpayerProfile'))
const CaseDetail = lazy(() => import('./pages/CaseDetail'))
const FraudGraph = lazy(() => import('./pages/FraudGraph'))
const ChainDetail = lazy(() => import('./pages/ChainDetail'))
const Performance = lazy(() => import('./pages/Performance'))
const Runs = lazy(() => import('./pages/Runs'))

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
          <Route index element={<Overview />} />
          <Route path="taxpayers" element={<Taxpayers />} />
          <Route path="taxpayers/:gstin" element={<TaxpayerProfile />} />
          <Route path="cases/:gstin" element={<CaseDetail />} />
          <Route path="graph" element={<FraudGraph />} />
          <Route path="chains/:id" element={<ChainDetail />} />
          <Route path="performance" element={<Performance />} />
          <Route path="runs" element={<Runs />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import { AppShell, PageSkeleton } from './components/ui'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'

// Screens load on first visit, so the Leaflet map and the chart code only ship with the pages that use them.
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const Quality = lazy(() => import('./pages/Quality.jsx'))
const NetworkPage = lazy(() => import('./pages/NetworkPage.jsx'))
const Forecast = lazy(() => import('./pages/Forecast.jsx'))
const Leaks = lazy(() => import('./pages/Leaks.jsx'))
const Evaluation = lazy(() => import('./pages/Evaluation.jsx'))

function Protected() {
  const { user, ready } = useAuth()
  const loc = useLocation()
  if (!ready) return <PageSkeleton kpis={3} blocks={1} />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return <Outlet />
}

export default function App() {
  return (
    <Suspense fallback={<PageSkeleton kpis={3} blocks={1} />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route element={<Protected />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/quality" element={<Quality />} />
            <Route path="/network" element={<NetworkPage />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/leaks" element={<Leaks />} />
            <Route path="/evaluation" element={<Evaluation />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

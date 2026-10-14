import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import { AppShell } from './components/ui'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Targets from './pages/Targets'
import Scans from './pages/Scans'
// Scan detail pulls in the charts library, so it loads on demand.
const ScanView = lazy(() => import('./pages/ScanView'))

// Everything under /app needs a signed-in user; anything else goes to the login page.
function Protected({ children }) {
  const { email, ready } = useAuth()
  if (!ready) {
    return (
      <div className="page-loader">
        <span className="spinner" role="status" aria-label="Loading" />
      </div>
    )
  }
  if (!email) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/app"
        element={
          <Protected>
            <AppShell />
          </Protected>
        }
      >
        <Route index element={<Navigate to="targets" replace />} />
        <Route path="targets" element={<Targets />} />
        <Route path="scans" element={<Scans />} />
        <Route
          path="scans/:id"
          element={
            <Suspense fallback={<div className="page-loader"><span className="spinner" role="status" aria-label="Loading" /></div>}>
              <ScanView />
            </Suspense>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

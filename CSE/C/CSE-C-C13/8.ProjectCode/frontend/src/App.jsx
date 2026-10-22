import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './lib/auth'
import { AppShell } from './components/ui'
import { Skeleton } from './components/ui'
import UnlockGate from './features/UnlockGate'

const Landing = lazy(() => import('./pages/Landing'))
const Auth = lazy(() => import('./pages/Auth'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Files = lazy(() => import('./pages/Files'))
const FileDetail = lazy(() => import('./pages/FileDetail'))
const Audit = lazy(() => import('./pages/Audit'))
const Security = lazy(() => import('./pages/Security'))
const NotFound = lazy(() => import('./pages/NotFound'))

function Splash() {
  return (
    <div className="container" style={{ paddingTop: 80 }} aria-busy="true" aria-label="Loading">
      <Skeleton height={28} width={260} />
      <Skeleton height={16} width={420} style={{ marginTop: 14 }} />
      <Skeleton height={220} style={{ marginTop: 28 }} />
    </div>
  )
}

function Protected({ children }) {
  const { user, booting } = useAuth()
  const loc = useLocation()
  if (booting) return <Splash />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}

export default function App() {
  return (
    <Suspense fallback={<Splash />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Auth mode="login" />} />
        <Route path="/register" element={<Auth mode="register" />} />
        <Route
          path="/app"
          element={
            <Protected>
              <UnlockGate>
                <AppShell />
              </UnlockGate>
            </Protected>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="files" element={<Files mode="owned" />} />
          <Route path="shared" element={<Files mode="shared" />} />
          <Route path="files/:id" element={<FileDetail />} />
          <Route path="audit" element={<Audit />} />
          <Route path="security" element={<Security />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

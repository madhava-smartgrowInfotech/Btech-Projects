import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './lib/auth'
import { AppShell, PageSkeleton } from './components/ui'

// Every screen is code-split; charts, motion and the graph canvas load as separate chunks on demand.
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Overview = lazy(() => import('./pages/Overview'))
const GraphData = lazy(() => import('./pages/GraphData'))
const Accounts = lazy(() => import('./pages/Accounts'))
const AccountDetail = lazy(() => import('./pages/AccountDetail'))
const Clusters = lazy(() => import('./pages/Clusters'))
const ClusterDetail = lazy(() => import('./pages/ClusterDetail'))
const Queue = lazy(() => import('./pages/Queue'))
const Models = lazy(() => import('./pages/Models'))
const NotFound = lazy(() => import('./pages/NotFound'))

export default function App() {
  return (
    <Suspense
      fallback={
        <div className="container" style={{ paddingTop: 48 }}>
          <PageSkeleton />
        </div>
      }
    >
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
          <Route index element={<Overview />} />
          <Route path="graph" element={<GraphData />} />
          <Route path="accounts" element={<Accounts />} />
          <Route path="accounts/:id" element={<AccountDetail />} />
          <Route path="clusters" element={<Clusters />} />
          <Route path="clusters/:id" element={<ClusterDetail />} />
          <Route path="queue" element={<Queue />} />
          <Route path="models" element={<Models />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="/dashboard" element={<Navigate to="/app" replace />} />
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  )
}

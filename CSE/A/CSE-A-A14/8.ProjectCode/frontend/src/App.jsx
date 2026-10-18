import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './lib/auth'
import { AppShell } from './components/ui'
import { PageSkeleton } from './components/ui'

// Every screen is code-split; charts, motion and effects load as separate chunks on demand.
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const DataUpload = lazy(() => import('./pages/DataUpload'))
const Explore = lazy(() => import('./pages/Explore'))
const Train = lazy(() => import('./pages/Train'))
const Evaluation = lazy(() => import('./pages/Evaluation'))
const Risk = lazy(() => import('./pages/Risk'))
const Customer360 = lazy(() => import('./pages/Customer360'))
const Explain = lazy(() => import('./pages/Explain'))
const WhatIf = lazy(() => import('./pages/WhatIf'))
const Retention = lazy(() => import('./pages/Retention'))
const Batch = lazy(() => import('./pages/Batch'))
const Monitoring = lazy(() => import('./pages/Monitoring'))
const About = lazy(() => import('./pages/About'))
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
          <Route index element={<Dashboard />} />
          <Route path="data" element={<DataUpload />} />
          <Route path="eda" element={<Explore />} />
          <Route path="train" element={<Train />} />
          <Route path="evaluation" element={<Evaluation />} />
          <Route path="risk" element={<Risk />} />
          <Route path="customer" element={<Customer360 />} />
          <Route path="explain" element={<Explain />} />
          <Route path="whatif" element={<WhatIf />} />
          <Route path="retention" element={<Retention />} />
          <Route path="batch" element={<Batch />} />
          <Route path="monitoring" element={<Monitoring />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="/dashboard" element={<Navigate to="/app" replace />} />
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  )
}

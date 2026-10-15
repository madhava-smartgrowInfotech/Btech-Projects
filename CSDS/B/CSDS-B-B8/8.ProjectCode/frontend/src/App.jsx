import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './lib/auth'
import { MonitorProvider } from './lib/monitor'
import { AppShell } from './components/ui'
import { Skeleton } from './components/ui'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'

// charts and the heavier screens load on demand
const Monitor = lazy(() => import('./pages/Monitor.jsx'))
const Alerts = lazy(() => import('./pages/Alerts.jsx'))
const Contacts = lazy(() => import('./pages/Contacts.jsx'))
const Report = lazy(() => import('./pages/Report.jsx'))
const Performance = lazy(() => import('./pages/Performance.jsx'))

function PageFallback() {
  return (
    <div aria-busy="true" aria-label="Loading page" className="stack">
      <Skeleton height={34} width="40%" />
      <Skeleton height={220} />
    </div>
  )
}

function Protected() {
  return (
    <RequireAuth>
      <MonitorProvider>
        <AppShell />
      </MonitorProvider>
    </RequireAuth>
  )
}

const page = (el) => <Suspense fallback={<PageFallback />}>{el}</Suspense>

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/app" element={<Protected />}>
        <Route index element={<Navigate to="monitor" replace />} />
        <Route path="monitor" element={page(<Monitor />)} />
        <Route path="alerts" element={page(<Alerts />)} />
        <Route path="contacts" element={page(<Contacts />)} />
        <Route path="report" element={page(<Report />)} />
        <Route path="performance" element={page(<Performance />)} />
      </Route>
      {['monitor', 'alerts', 'contacts', 'report', 'performance'].map((p) => (
        <Route key={p} path={`/${p}`} element={<Navigate to={`/app/${p}`} replace />} />
      ))}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

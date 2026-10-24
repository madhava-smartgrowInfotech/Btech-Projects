import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import AppShell from './components/ui/AppShell'
import { PageSkeleton } from './components/ui/feedback'
import { RequireAuth } from './lib/auth'
import { LiveProvider } from './lib/live'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Overview = lazy(() => import('./pages/Overview'))
const Detections = lazy(() => import('./pages/Detections'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Health = lazy(() => import('./pages/Health'))
const Mitigation = lazy(() => import('./pages/Mitigation'))
const Model = lazy(() => import('./pages/Model'))
const Settings = lazy(() => import('./pages/Settings'))
const NotFound = lazy(() => import('./pages/NotFound'))

function Console() {
  return (
    <RequireAuth>
      <LiveProvider>
        <AppShell />
      </LiveProvider>
    </RequireAuth>
  )
}

export default function App() {
  return (
    <Suspense fallback={<div className="p-8"><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/app" element={<Console />}>
          <Route index element={<Overview />} />
          <Route path="detections" element={<Detections />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="health" element={<Health />} />
          <Route path="mitigation" element={<Mitigation />} />
          <Route path="model" element={<Model />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  )
}

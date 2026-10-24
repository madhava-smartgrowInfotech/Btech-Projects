import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/ui/AppShell'
import { PageSkeleton } from './components/ui/feedback'
import { RequireAuth } from './lib/auth'
import { LiveProvider } from './lib/live'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Live = lazy(() => import('./pages/Live'))
const Benchmark = lazy(() => import('./pages/Benchmark'))
const Vision = lazy(() => import('./pages/Vision'))
const Prediction = lazy(() => import('./pages/Prediction'))
const Violations = lazy(() => import('./pages/Violations'))
const About = lazy(() => import('./pages/About'))

function Protected() {
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
        <Route path="/app" element={<Protected />}>
          <Route index element={<Live />} />
          <Route path="benchmark" element={<Benchmark />} />
          <Route path="vision" element={<Vision />} />
          <Route path="prediction" element={<Prediction />} />
          <Route path="violations" element={<Violations />} />
          <Route path="about" element={<About />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

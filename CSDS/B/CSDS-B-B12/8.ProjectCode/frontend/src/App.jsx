import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell } from './components/ui/Layout.jsx'
import { SkeletonBlock } from './components/ui/Feedback.jsx'
import { useAuth } from './lib/auth.jsx'

// Pages load on demand so the landing page and sign-in stay light; charts only load with the pages that use them.
const Landing = lazy(() => import('./pages/Landing.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const NewScan = lazy(() => import('./pages/NewScan.jsx'))
const Result = lazy(() => import('./pages/Result.jsx'))
const Report = lazy(() => import('./pages/Report.jsx'))
const Patients = lazy(() => import('./pages/Patients.jsx'))
const PatientDetail = lazy(() => import('./pages/PatientDetail.jsx'))
const Performance = lazy(() => import('./pages/Performance.jsx'))
const Audit = lazy(() => import('./pages/Audit.jsx'))

function Private({ children, role }) {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  if (role && user.role !== role) return <Navigate to="/scan" replace />
  return <AppShell>{children}</AppShell>
}

function Fallback() {
  return (
    <div className="container" style={{ paddingTop: 48 }}>
      <SkeletonBlock rows={4} label="Loading page" />
    </div>
  )
}

export default function App() {
  return (
    <Suspense fallback={<Fallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/scan" element={<Private><NewScan /></Private>} />
        <Route path="/scans/:id" element={<Private><Result /></Private>} />
        <Route path="/scans/:id/report" element={<Private role="doctor"><Report /></Private>} />
        <Route path="/patients" element={<Private><Patients /></Private>} />
        <Route path="/patients/:id" element={<Private><PatientDetail /></Private>} />
        <Route path="/performance" element={<Private><Performance /></Private>} />
        <Route path="/audit" element={<Private role="doctor"><Audit /></Private>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

import { lazy } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import AppShell from './components/ui/AppShell'
import { useAuth } from './lib/auth'
import Landing from './pages/Landing'
import Login from './pages/Login'

// Screens load on first visit, so the landing page does not pay for charts and three.js.
const Studio = lazy(() => import('./pages/Studio'))
const Lab = lazy(() => import('./pages/Lab'))
const Live = lazy(() => import('./pages/Live'))
const Benchmark = lazy(() => import('./pages/Benchmark'))

function Protected({ children }) {
  const { user } = useAuth()
  const { pathname } = useLocation()
  return user ? children : <Navigate to="/login" replace state={{ from: pathname }} />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route element={<Protected><AppShell /></Protected>}>
        <Route path="/studio" element={<Studio />} />
        <Route path="/lab" element={<Lab />} />
        <Route path="/live" element={<Live />} />
        <Route path="/benchmark" element={<Benchmark />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

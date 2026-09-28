import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import { Spinner } from './components/ui'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Targets from './pages/Targets'
import Scans from './pages/Scans'
import ScanView from './pages/ScanView'

function Protected({ children }) {
  const { email, ready } = useAuth()
  if (!ready) return <div className="p-10"><Spinner /></div>
  if (!email) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/app/targets" element={<Protected><Targets /></Protected>} />
      <Route path="/app/scans" element={<Protected><Scans /></Protected>} />
      <Route path="/app/scans/:id" element={<Protected><ScanView /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

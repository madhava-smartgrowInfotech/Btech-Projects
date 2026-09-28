import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Quality from './pages/Quality.jsx'
import NetworkPage from './pages/NetworkPage.jsx'
import Forecast from './pages/Forecast.jsx'
import Leaks from './pages/Leaks.jsx'

function Protected({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/quality" element={<Protected><Quality /></Protected>} />
      <Route path="/network" element={<Protected><NetworkPage /></Protected>} />
      <Route path="/forecast" element={<Protected><Forecast /></Protected>} />
      <Route path="/leaks" element={<Protected><Leaks /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

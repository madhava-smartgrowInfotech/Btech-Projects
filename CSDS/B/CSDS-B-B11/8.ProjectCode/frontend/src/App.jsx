import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import AuthPage from './pages/AuthPage'
import ProfileWizard from './pages/ProfileWizard'
import Dashboard from './pages/Dashboard'
import PlanPage from './pages/PlanPage'
import FoodLog from './pages/FoodLog'
import Progress from './pages/Progress'

function Private({ children, needProfile = true }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (needProfile && !user.has_profile) return <Navigate to="/profile" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Landing />} />
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route path="/profile" element={<Private needProfile={false}><ProfileWizard /></Private>} />
      <Route path="/dashboard" element={<Private><Dashboard /></Private>} />
      <Route path="/plan" element={<Private><PlanPage /></Private>} />
      <Route path="/log" element={<Private><FoodLog /></Private>} />
      <Route path="/progress" element={<Private><Progress /></Private>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

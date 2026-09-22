import { Navigate, Route, Routes } from 'react-router-dom'
import { homeFor, useAuth } from './auth.jsx'
import Layout from './components/Layout.jsx'
import Analytics from './pages/Analytics.jsx'
import ComplaintDetail from './pages/ComplaintDetail.jsx'
import FileComplaint from './pages/FileComplaint.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Queue from './pages/Queue.jsx'
import Track from './pages/Track.jsx'

function Protected({ roles, children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to={homeFor(user)} replace />
  return <Layout>{children}</Layout>
}

const STAFF = ['officer', 'admin']

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/file" element={<Protected roles={['citizen']}><FileComplaint /></Protected>} />
      <Route path="/track" element={<Protected roles={['citizen']}><Track /></Protected>} />
      <Route path="/track/:trackingId" element={<Protected roles={['citizen']}><Track /></Protected>} />
      <Route path="/queue" element={<Protected roles={STAFF}><Queue /></Protected>} />
      <Route path="/complaints/:id" element={<Protected roles={STAFF}><ComplaintDetail /></Protected>} />
      <Route path="/analytics" element={<Protected roles={STAFF}><Analytics /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

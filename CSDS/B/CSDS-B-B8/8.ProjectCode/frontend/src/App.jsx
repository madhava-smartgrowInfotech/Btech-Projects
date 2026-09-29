import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Monitor from './pages/Monitor.jsx'
import Alerts from './pages/Alerts.jsx'
import Contacts from './pages/Contacts.jsx'
import Report from './pages/Report.jsx'
import Performance from './pages/Performance.jsx'

function Protected({ children }) {
  if (!localStorage.getItem('cw_token')) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/monitor" element={<Protected><Monitor /></Protected>} />
      <Route path="/alerts" element={<Protected><Alerts /></Protected>} />
      <Route path="/contacts" element={<Protected><Contacts /></Protected>} />
      <Route path="/report" element={<Protected><Report /></Protected>} />
      <Route path="/performance" element={<Protected><Performance /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

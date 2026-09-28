import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Calls from './pages/Calls.jsx'
import CallDetail from './pages/CallDetail.jsx'
import Studio from './pages/Studio.jsx'
import Analytics from './pages/Analytics.jsx'
import Performance from './pages/Performance.jsx'

function RequireAuth({ children }) {
  return localStorage.getItem('cs_token') ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/calls" element={<Calls />} />
        <Route path="/calls/:id" element={<CallDetail />} />
        <Route path="/studio" element={<Studio />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/performance" element={<Performance />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

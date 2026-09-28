import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Conversation from './pages/Conversation.jsx'
import Practice from './pages/Practice.jsx'
import History from './pages/History.jsx'
import Performance from './pages/Performance.jsx'

function Private({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login mode="login" />} />
      <Route path="/register" element={<Login mode="register" />} />
      <Route element={<Private><Layout /></Private>}>
        <Route path="/app" element={<Conversation />} />
        <Route path="/app/practice" element={<Practice />} />
        <Route path="/app/history" element={<History />} />
        <Route path="/app/performance" element={<Performance />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

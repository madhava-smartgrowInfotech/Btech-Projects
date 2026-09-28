import { useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Admissions from './pages/Admissions.jsx'
import Forecasts from './pages/Forecasts.jsx'
import Allocation from './pages/Allocation.jsx'
import Performance from './pages/Performance.jsx'

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('hs_user'))
  } catch {
    return null
  }
}

export default function App() {
  const [user, setUser] = useState(readUser)

  const onLogin = ({ token, user }) => {
    localStorage.setItem('hs_token', token)
    localStorage.setItem('hs_user', JSON.stringify(user))
    setUser(user)
  }
  const onLogout = () => {
    localStorage.removeItem('hs_token')
    localStorage.removeItem('hs_user')
    setUser(null)
  }

  const guard = (el) => (user ? <Layout user={user} onLogout={onLogout}>{el}</Layout> : <Navigate to="/login" replace />)

  return (
    <Routes>
      <Route path="/" element={<Landing user={user} />} />
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login onLogin={onLogin} />} />
      <Route path="/dashboard" element={guard(<Dashboard user={user} />)} />
      <Route path="/admissions" element={guard(<Admissions user={user} />)} />
      <Route path="/forecasts" element={guard(<Forecasts user={user} />)} />
      <Route path="/allocation" element={guard(<Allocation user={user} />)} />
      <Route path="/performance" element={guard(<Performance user={user} />)} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

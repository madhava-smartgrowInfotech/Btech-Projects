import { createContext, useContext, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import CaseDetail from './pages/CaseDetail'
import ChainDetail from './pages/ChainDetail'
import FraudGraph from './pages/FraudGraph'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Overview from './pages/Overview'
import Performance from './pages/Performance'
import TaxpayerProfile from './pages/TaxpayerProfile'
import Taxpayers from './pages/Taxpayers'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('ts_user'))
  } catch {
    return null
  }
}

export default function App() {
  const [user, setUser] = useState(() => (localStorage.getItem('ts_token') ? readUser() : null))
  const auth = {
    user,
    signIn(token, u) {
      localStorage.setItem('ts_token', token)
      localStorage.setItem('ts_user', JSON.stringify(u))
      setUser(u)
    },
    signOut() {
      localStorage.removeItem('ts_token')
      localStorage.removeItem('ts_user')
      setUser(null)
    },
  }
  const guard = (el) => (user ? el : <Navigate to="/login" replace />)
  return (
    <AuthContext.Provider value={auth}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={user ? <Navigate to="/app" replace /> : <Login />} />
        <Route path="/app" element={guard(<Layout />)}>
          <Route index element={<Overview />} />
          <Route path="taxpayers" element={<Taxpayers />} />
          <Route path="taxpayers/:gstin" element={<TaxpayerProfile />} />
          <Route path="cases/:gstin" element={<CaseDetail />} />
          <Route path="graph" element={<FraudGraph />} />
          <Route path="chains/:id" element={<ChainDetail />} />
          <Route path="performance" element={<Performance />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthContext.Provider>
  )
}

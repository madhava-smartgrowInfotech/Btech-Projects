import { createContext, useContext, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import PatientPage from './pages/PatientPage.jsx'
import DoctorPage from './pages/DoctorPage.jsx'
import HospitalConsole from './pages/HospitalConsole.jsx'
import AuditPage from './pages/AuditPage.jsx'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export const HOME = { patient: '/patient', doctor: '/doctor', staff: '/hospital', admin: '/hospital' }

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('uh_user'))
  } catch {
    return null
  }
}

function Protected({ roles, children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to={HOME[user.role]} replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  const [user, setUser] = useState(readUser)
  const login = (token, u) => {
    localStorage.setItem('uh_token', token)
    localStorage.setItem('uh_user', JSON.stringify(u))
    setUser(u)
  }
  const logout = () => {
    localStorage.removeItem('uh_token')
    localStorage.removeItem('uh_user')
    setUser(null)
  }
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/patient" element={<Protected roles={['patient']}><PatientPage /></Protected>} />
        <Route path="/doctor" element={<Protected roles={['doctor']}><DoctorPage /></Protected>} />
        <Route path="/hospital" element={<Protected roles={['staff', 'admin']}><HospitalConsole /></Protected>} />
        <Route path="/audit" element={<Protected><AuditPage /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthContext.Provider>
  )
}

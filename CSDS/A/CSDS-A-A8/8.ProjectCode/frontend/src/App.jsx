import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import { getUser } from './api.js'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Mri from './pages/Mri.jsx'
import LabelEfficiency from './pages/LabelEfficiency.jsx'
import Dna from './pages/Dna.jsx'
import StrMatch from './pages/StrMatch.jsx'
import Performance from './pages/Performance.jsx'

function Protected({ children }) {
  return getUser() ? <Layout>{children}</Layout> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/mri" element={<Protected><Mri /></Protected>} />
      <Route path="/label-efficiency" element={<Protected><LabelEfficiency /></Protected>} />
      <Route path="/dna" element={<Protected><Dna /></Protected>} />
      <Route path="/str" element={<Protected><StrMatch /></Protected>} />
      <Route path="/performance" element={<Protected><Performance /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

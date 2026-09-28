import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import NewScreening from './pages/NewScreening.jsx'
import Result from './pages/Result.jsx'
import Report from './pages/Report.jsx'
import Patients from './pages/Patients.jsx'
import PatientDetail from './pages/PatientDetail.jsx'
import Performance from './pages/Performance.jsx'

function RequireAuth({ children }) {
  return localStorage.getItem('rg_token') ? children : <Navigate to="/login" replace />
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
        <Route path="/screening/new" element={<NewScreening />} />
        <Route path="/screenings/:id" element={<Result />} />
        <Route path="/screenings/:id/report" element={<Report />} />
        <Route path="/patients" element={<Patients />} />
        <Route path="/patients/:id" element={<PatientDetail />} />
        <Route path="/performance" element={<Performance />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

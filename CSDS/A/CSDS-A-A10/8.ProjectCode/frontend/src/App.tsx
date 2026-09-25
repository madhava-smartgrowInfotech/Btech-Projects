import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { Toaster } from '@/components/ui/Toaster'
import AdminDashboard from '@/pages/AdminDashboard'
import DoctorDashboard from '@/pages/DoctorDashboard'
import Landing from '@/pages/Landing'
import LabDashboard from '@/pages/LabDashboard'
import Login from '@/pages/Login'
import NurseDashboard from '@/pages/NurseDashboard'
import ReceptionDashboard from '@/pages/ReceptionDashboard'
import WaitingBoard from '@/pages/WaitingBoard'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/board" element={<WaitingBoard />} />

        <Route
          path="/app/admin"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/app/doctor"
          element={
            <ProtectedRoute roles={['doctor']}>
              <DoctorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/app/nurse"
          element={
            <ProtectedRoute roles={['nurse']}>
              <NurseDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/app/lab"
          element={
            <ProtectedRoute roles={['lab_tech']}>
              <LabDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/app/reception"
          element={
            <ProtectedRoute roles={['reception']}>
              <ReceptionDashboard />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}

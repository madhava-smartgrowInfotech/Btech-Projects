import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './index.css'
import { AuthProvider, RequireRole } from './auth'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Book from './pages/Book'
import MyTokens from './pages/MyTokens'
import TokenDetail from './pages/TokenDetail'
import Console from './pages/Console'
import Referrals from './pages/Referrals'
import Dashboard from './pages/Dashboard'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/book" element={<RequireRole roles={['patient']}><Book /></RequireRole>} />
            <Route path="/tokens" element={<RequireRole roles={['patient']}><MyTokens /></RequireRole>} />
            <Route path="/tokens/:id" element={<RequireRole roles={['patient']}><TokenDetail /></RequireRole>} />
            <Route path="/console" element={<RequireRole roles={['staff', 'admin']}><Console /></RequireRole>} />
            <Route path="/referrals" element={<RequireRole roles={['patient', 'staff', 'admin']}><Referrals /></RequireRole>} />
            <Route path="/dashboard" element={<RequireRole roles={['admin']}><Dashboard /></RequireRole>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)

import { lazy, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import './index.css'
import { AuthProvider, RequireRole, RequireUser } from './auth'
import AppShell from './components/ui/AppShell'
import { ToastProvider } from './components/ui/feedback'
import Layout from './components/Layout'
import { ThemeProvider } from './lib/theme'
import Landing from './pages/Landing'
import Login from './pages/Login'

// heavier screens (maps, charts, live queue) are split into their own chunks
const Book = lazy(() => import('./pages/Book'))
const MyTokens = lazy(() => import('./pages/MyTokens'))
const TokenDetail = lazy(() => import('./pages/TokenDetail'))
const Console = lazy(() => import('./pages/Console'))
const Referrals = lazy(() => import('./pages/Referrals'))
const Dashboard = lazy(() => import('./pages/Dashboard'))

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<Layout />}>
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
              </Route>
              <Route element={<RequireUser><AppShell /></RequireUser>}>
                <Route path="/book" element={<RequireRole roles={['patient']}><Book /></RequireRole>} />
                <Route path="/tokens" element={<RequireRole roles={['patient']}><MyTokens /></RequireRole>} />
                <Route path="/tokens/:id" element={<RequireRole roles={['patient', 'staff', 'admin']}><TokenDetail /></RequireRole>} />
                <Route path="/console" element={<RequireRole roles={['staff', 'admin']}><Console /></RequireRole>} />
                <Route path="/referrals" element={<RequireRole roles={['patient', 'staff', 'admin']}><Referrals /></RequireRole>} />
                <Route path="/dashboard" element={<RequireRole roles={['admin']}><Dashboard /></RequireRole>} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)

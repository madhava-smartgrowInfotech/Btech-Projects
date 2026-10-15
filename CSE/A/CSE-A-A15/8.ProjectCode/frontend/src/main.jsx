import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './index.css'
import RequireAuth from './components/RequireAuth'
import AppShell from './components/ui/AppShell'
import { PageSkeleton, ToastProvider } from './components/ui/feedback'
import { ThemeProvider } from './lib/theme'

// every screen is its own chunk, so the three.js and chart code only loads where it is used
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Keys = lazy(() => import('./pages/Keys'))
const Send = lazy(() => import('./pages/Send'))
const Receive = lazy(() => import('./pages/Receive'))
const Analysis = lazy(() => import('./pages/Analysis'))
const Robustness = lazy(() => import('./pages/Robustness'))
const Log = lazy(() => import('./pages/Log'))

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <Suspense fallback={<PageSkeleton />}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route element={<RequireAuth><AppShell /></RequireAuth>}>
                <Route path="/keys" element={<Keys />} />
                <Route path="/send" element={<Send />} />
                <Route path="/receive" element={<Receive />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/robustness" element={<Robustness />} />
                <Route path="/log" element={<Log />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  </React.StrictMode>,
)

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import App from './App.jsx'
import { AuthProvider } from './auth.jsx'
import { ToastProvider } from './components/ui'
import { ThemeProvider } from './lib/theme.jsx'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      {/* reducedMotion="user" follows the OS setting: springs collapse to fades */}
      <MotionConfig reducedMotion="user">
        <ToastProvider>
          <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <AuthProvider>
              <App />
            </AuthProvider>
          </BrowserRouter>
        </ToastProvider>
      </MotionConfig>
    </ThemeProvider>
  </React.StrictMode>,
)

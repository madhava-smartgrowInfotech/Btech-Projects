import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import './styles/index.css'
import './styles/app.css'
import { ThemeProvider } from './lib/theme'
import { AuthProvider } from './lib/auth'
import { ToastProvider } from './components/ui'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
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
  </StrictMode>,
)

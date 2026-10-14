import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import App from './App'
import { ThemeProvider } from './lib/theme'
import { ToastProvider } from './components/ui/Toast'
import './styles/index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      {/* reducedMotion="user": transform/layout animation collapses to opacity when the OS asks for less motion */}
      <MotionConfig reducedMotion="user">
        <ToastProvider>
          <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <App />
          </BrowserRouter>
        </ToastProvider>
      </MotionConfig>
    </ThemeProvider>
  </StrictMode>,
)

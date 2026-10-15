import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import App from './App'
import { ThemeProvider } from './lib/theme'
import { HealthProvider } from './lib/health'
import { ToastProvider } from './components/ui'
import './styles/index.css'
import './styles/app.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <MotionConfig reducedMotion="user">
      <ThemeProvider>
        <ToastProvider>
          <HealthProvider>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </HealthProvider>
        </ToastProvider>
      </ThemeProvider>
    </MotionConfig>
  </StrictMode>,
)

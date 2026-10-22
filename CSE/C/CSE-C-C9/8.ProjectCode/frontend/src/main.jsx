import '@fontsource-variable/plus-jakarta-sans'
import '@fontsource-variable/inter'
import './styles/index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MotionConfig } from 'framer-motion'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from './lib/theme'
import { ToastProvider } from './components/ui'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <MotionConfig reducedMotion="user">
      <ThemeProvider>
        <ToastProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    </MotionConfig>
  </StrictMode>,
)

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { AuthProvider } from './lib/auth'
import { ThemeProvider } from './lib/theme'
import { ToastProvider } from './components/ui/Toast'
import { SmoothScroll } from './components/motion'
import './styles/tokens.css'
import './styles/global.css'
import './styles/app.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <SmoothScroll>
              <App />
            </SmoothScroll>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>,
)

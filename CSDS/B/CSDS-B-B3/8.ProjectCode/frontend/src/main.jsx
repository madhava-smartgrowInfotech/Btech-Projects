import '@fontsource-variable/inter'
import '@fontsource-variable/sora'
import '@fontsource-variable/jetbrains-mono'
import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'
import './styles/landing.css'
import './styles/app.css'
import { ThemeProvider } from './lib/theme'
import { AuthProvider } from './lib/auth'
import { ToastProvider } from './components/ui'
import App from './App'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  </React.StrictMode>,
)

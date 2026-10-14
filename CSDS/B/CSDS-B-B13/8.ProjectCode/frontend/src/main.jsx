import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './auth'
import { ThemeProvider } from './lib/theme'
import { ToastProvider } from './components/ui'
import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'
import './styles/landing.css'
import './styles/app.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  </React.StrictMode>,
)

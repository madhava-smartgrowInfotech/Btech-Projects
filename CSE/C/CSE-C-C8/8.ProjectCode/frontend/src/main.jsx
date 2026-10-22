import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'
import './styles/landing.css'
import './styles/peerscope.css'
import { ThemeProvider } from './lib/theme'
import { ToastProvider } from './components/ui'
import { StatsProvider } from './lib/stats'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <StatsProvider>
          <BrowserRouter>
            <div className="grain" aria-hidden="true" />
            <App />
          </BrowserRouter>
        </StatsProvider>
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)

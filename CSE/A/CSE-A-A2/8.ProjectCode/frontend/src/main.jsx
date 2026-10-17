import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource/archivo-black/400.css'
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-sans/700.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/600.css'
import './styles/global.css' // pulls in tokens.css
import App from './App'
import { SmoothScroll } from './components/motion'
import { ToastProvider } from './components/ui'
import { AuthProvider, useAuth } from './lib/auth'
import { ThemeProvider } from './lib/theme'
import { MonitorProvider } from './state/MonitorContext'

// Remount the monitor state on sign-in/out so one user's readings and alerts never show for the next.
function Session() {
  const { user } = useAuth()
  return (
    <MonitorProvider key={user?.id ?? 'anon'}>
      <App />
    </MonitorProvider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <SmoothScroll>
        <BrowserRouter>
          <ToastProvider>
            <AuthProvider>
              <Session />
            </AuthProvider>
          </ToastProvider>
        </BrowserRouter>
      </SmoothScroll>
    </ThemeProvider>
  </StrictMode>,
)

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
import { ThemeProvider } from './lib/theme'
import { MonitorProvider } from './state/MonitorContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <SmoothScroll>
        <BrowserRouter>
          <ToastProvider>
            <MonitorProvider>
              <App />
            </MonitorProvider>
          </ToastProvider>
        </BrowserRouter>
      </SmoothScroll>
    </ThemeProvider>
  </StrictMode>,
)

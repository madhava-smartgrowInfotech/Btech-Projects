import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './styles/index.css'
import { ThemeProvider } from './lib/theme'
import { ToastProvider } from './components/ui'
import { LabProvider } from './lib/lab'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <LabProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </LabProvider>
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)

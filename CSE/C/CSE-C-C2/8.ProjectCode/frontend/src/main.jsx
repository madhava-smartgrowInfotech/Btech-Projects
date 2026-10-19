import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './styles/global.css'
import './styles/app.css'
import { ThemeProvider } from './lib/theme'
import { MetaProvider } from './lib/meta'
import { ToastProvider } from './components/ui'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <MetaProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </MetaProvider>
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)

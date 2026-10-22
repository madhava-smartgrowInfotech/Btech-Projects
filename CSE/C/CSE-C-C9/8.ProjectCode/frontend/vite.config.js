import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from ../.env (PORT = Flask API, FRONTEND_PORT = this app); defaults 8409 / 5409.
// Dev and preview both proxy the API so the browser only ever talks to the frontend port.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const api = `http://127.0.0.1:${env.PORT || 8409}`
  const port = Number(env.FRONTEND_PORT || 5409)
  const proxy = { '/api': api, '/artifacts': api, '/health': api }
  return {
    plugins: [react()],
    server: { port, strictPort: true, host: '127.0.0.1', proxy },
    preview: { port, strictPort: true, host: '127.0.0.1', proxy },
    build: { chunkSizeWarningLimit: 900 },
  }
})

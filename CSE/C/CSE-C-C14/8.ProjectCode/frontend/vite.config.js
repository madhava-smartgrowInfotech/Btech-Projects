import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from ../.env (FRONTEND_PORT / VERIVISION_PORT) so run.bat and the UI agree.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  // Docker sets VERIVISION_API_URL (http://api:8414) and FRONTEND_HOST (0.0.0.0)
  const backend = process.env.VERIVISION_API_URL || `http://127.0.0.1:${env.VERIVISION_PORT || 8414}`
  const proxy = {
    '/api': { target: backend, changeOrigin: true, timeout: 600000, proxyTimeout: 600000 },
    '/health': { target: backend, changeOrigin: true },
    '/artifacts': { target: backend, changeOrigin: true },
  }
  const port = Number(env.FRONTEND_PORT || 5414)
  return {
    plugins: [react()],
    server: { port, strictPort: true, host: process.env.FRONTEND_HOST || '127.0.0.1', proxy },
    preview: { port, strictPort: true, host: process.env.FRONTEND_HOST || '127.0.0.1', proxy },
    build: { chunkSizeWarningLimit: 900 },
  }
})

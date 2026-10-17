import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from ../.env (BACKEND_PORT / FRONTEND_PORT) so run.bat and Vite agree.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8303'
  const frontend = Number(env.FRONTEND_PORT || 5303)
  return {
    plugins: [react()],
    define: { 'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || `http://127.0.0.1:${backend}`) },
    server: { port: frontend, strictPort: true, host: '127.0.0.1' },
    preview: { port: frontend, strictPort: true, host: '127.0.0.1' },
    build: { chunkSizeWarningLimit: 1200 },
  }
})

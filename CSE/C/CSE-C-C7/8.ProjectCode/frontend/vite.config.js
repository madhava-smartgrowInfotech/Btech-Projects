import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from the project-level .env (BACKEND_PORT / FRONTEND_PORT).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = `http://127.0.0.1:${env.BACKEND_PORT || 8407}`
  const proxy = { '/api': backend, '/static': backend }
  const port = Number(env.FRONTEND_PORT || 5407)
  return {
    plugins: [react()],
    server: { port, strictPort: true, host: '127.0.0.1', proxy },
    preview: { port, strictPort: true, host: '127.0.0.1', proxy },
    build: { chunkSizeWarningLimit: 700 },
  }
})

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from the project-level .env (PORT = backend, FRONTEND_PORT = this dev server).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const api = `http://127.0.0.1:${env.PORT || 8402}`
  const port = Number(env.FRONTEND_PORT || 5402)
  return {
    plugins: [react()],
    server: { host: '127.0.0.1', port, strictPort: true, proxy: { '/api': api } },
    preview: { host: '127.0.0.1', port, strictPort: true, proxy: { '/api': api } },
    build: { chunkSizeWarningLimit: 700 },
  }
})

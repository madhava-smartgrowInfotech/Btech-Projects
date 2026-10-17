import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from ../.env (BACKEND_PORT / FRONTEND_PORT); defaults match the project spec.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = Number(env.BACKEND_PORT) || 8302
  const frontend = Number(env.FRONTEND_PORT) || 5302
  const proxy = { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: true } }
  return {
    plugins: [react()],
    server: { port: frontend, strictPort: true, proxy },
    preview: { port: frontend, strictPort: true, proxy },
    build: { chunkSizeWarningLimit: 900 },
  }
})

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// Ports come from ../.env (BACKEND_PORT / FRONTEND_PORT); defaults are this batch's fixed ports.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(process.cwd(), '..'), '')
  const backend = env.BACKEND_PORT || '8102'
  const port = Number(env.FRONTEND_PORT || 5102)
  return {
    plugins: [react()],
    server: {
      port,
      strictPort: true,
      host: true,
      proxy: { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: false } },
    },
    preview: { port, strictPort: true, proxy: { '/api': `http://127.0.0.1:${backend}` } },
    build: { chunkSizeWarningLimit: 700 },
  }
})

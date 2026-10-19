import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// Ports come from the project-level .env (run.bat reads the same file).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(import.meta.dirname, '..'), '')
  const backend = env.BACKEND_PORT || '8404'
  const frontend = Number(env.FRONTEND_PORT || 5404)
  const proxy = { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: true } }
  return {
    plugins: [react()],
    server: { port: frontend, strictPort: true, host: 'localhost', proxy },
    preview: { port: frontend, strictPort: true, host: 'localhost', proxy },
    build: { outDir: 'dist', chunkSizeWarningLimit: 700 },
  }
})

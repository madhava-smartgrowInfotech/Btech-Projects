import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const api = `http://127.0.0.1:${env.BACKEND_PORT || 8412}`
  const port = Number(env.FRONTEND_PORT || 5412)
  return {
    plugins: [react()],
    server: { port, strictPort: true, host: '127.0.0.1', proxy: { '/api': { target: api, changeOrigin: true } } },
    preview: { port, strictPort: true, host: '127.0.0.1', proxy: { '/api': { target: api, changeOrigin: true } } },
    build: { chunkSizeWarningLimit: 700 },
  }
})

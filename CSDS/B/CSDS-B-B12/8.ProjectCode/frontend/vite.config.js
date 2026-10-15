import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = `http://127.0.0.1:${env.BACKEND_PORT || 8212}`
  return {
    plugins: [react()],
    server: {
      port: Number(env.FRONTEND_PORT || 5212),
      strictPort: true,
      proxy: { '/api': { target: backend, changeOrigin: true, timeout: 300000, proxyTimeout: 300000 } },
    },
    preview: { port: Number(env.FRONTEND_PORT || 5212), strictPort: true },
  }
})

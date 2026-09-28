import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = `http://127.0.0.1:${env.BACKEND_PORT || 8210}`
  return {
    plugins: [react()],
    server: {
      port: Number(env.FRONTEND_PORT || 5210),
      strictPort: true,
      proxy: { '/api': { target: backend, changeOrigin: true, ws: true } },
    },
  }
})

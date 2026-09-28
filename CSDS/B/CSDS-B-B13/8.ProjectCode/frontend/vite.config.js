import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// Frontend on 5213, backend on 8213 (fixed ports; read from the project .env).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, resolve(process.cwd(), '..'), '')
  const backendPort = env.BACKEND_PORT || '8213'
  const frontendPort = parseInt(env.FRONTEND_PORT || '5213', 10)
  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      strictPort: true,
      proxy: {
        '/api': { target: `http://localhost:${backendPort}`, changeOrigin: true },
      },
    },
    preview: { port: frontendPort, strictPort: true },
  }
})

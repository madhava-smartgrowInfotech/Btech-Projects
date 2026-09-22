import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Ports come from the project .env (one level up)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8201'
  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: Number(env.FRONTEND_PORT || 5201),
      strictPort: true,
      proxy: { '/api': `http://127.0.0.1:${backend}` },
    },
    build: { chunkSizeWarningLimit: 800 },
    preview: { port: Number(env.FRONTEND_PORT || 5201), strictPort: true },
  }
})

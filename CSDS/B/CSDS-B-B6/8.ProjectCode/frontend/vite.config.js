import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Ports come from the project .env (one folder up).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8206'
  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: Number(env.FRONTEND_PORT || 5206),
      strictPort: true,
      proxy: { '/api': `http://127.0.0.1:${backend}` },
    },
    preview: { port: Number(env.FRONTEND_PORT || 5206), strictPort: true },
  }
})

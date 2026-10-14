import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Ports come from the project-root .env (backend 8214, frontend 5214).
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8214'
  return {
    plugins: [react()],
    server: {
      port: Number(env.FRONTEND_PORT || 5214),
      strictPort: true,
      proxy: { '/api': `http://127.0.0.1:${backend}` },
    },
    preview: { port: Number(env.FRONTEND_PORT || 5214), strictPort: true },
  }
})

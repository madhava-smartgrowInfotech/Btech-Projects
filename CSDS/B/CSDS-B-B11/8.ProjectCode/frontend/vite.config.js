import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Ports come from the project-level .env (see .env.example)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8211'
  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: Number(env.FRONTEND_PORT || 5211),
      strictPort: true,
      proxy: { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: true } },
    },
    preview: { port: Number(env.FRONTEND_PORT || 5211), strictPort: true },
  }
})

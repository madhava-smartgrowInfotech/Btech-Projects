import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Ports come from the project-root .env (FRONTEND_PORT / BACKEND_PORT)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8105'
  const port = Number(env.FRONTEND_PORT || 5105)
  return {
    plugins: [react(), tailwindcss()],
    server: {
      port,
      strictPort: true,
      proxy: { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: true } },
    },
    preview: { port, strictPort: true },
  }
})

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(({ mode }) => {
  // ports come from the project-level .env so backend and frontend always agree
  const env = loadEnv(mode, path.resolve(here, '..'), '')
  const backend = env.BACKEND_PORT || '8315'
  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: Number(env.FRONTEND_PORT || 5315),
      strictPort: true,
      proxy: { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: true } },
    },
  }
})

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// Ports come from ../.env (BACKEND_PORT / FRONTEND_PORT); defaults are this batch's fixed ports.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(process.cwd(), '..'), '')
  const backend = env.BACKEND_PORT || '8317'
  const port = Number(env.FRONTEND_PORT || 5317)
  return {
    plugins: [react()],
    server: {
      port,
      strictPort: true,
      host: true,
      proxy: { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: false } },
    },
    preview: { port, strictPort: true, proxy: { '/api': `http://127.0.0.1:${backend}` } },
    build: {
      chunkSizeWarningLimit: 700,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/recharts') || id.includes('node_modules/d3-') || id.includes('node_modules/victory-vendor')) return 'charts'
            if (id.includes('node_modules/gsap')) return 'gsap'
            if (id.includes('node_modules/framer-motion') || id.includes('node_modules/motion-')) return 'motion'
          },
        },
      },
    },
  }
})

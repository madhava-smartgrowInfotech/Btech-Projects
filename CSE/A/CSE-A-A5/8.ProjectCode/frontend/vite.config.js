import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, loadEnv } from 'vite'

// Ports come from ../.env (BACKEND_PORT / FRONTEND_PORT); defaults match the assigned 8305 / 5305.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = `http://${env.BACKEND_HOST || '127.0.0.1'}:${env.BACKEND_PORT || 8305}`
  const port = Number(env.FRONTEND_PORT || 5305)
  const proxy = { '/api': { target: backend, changeOrigin: true }, '/docs': backend, '/openapi.json': backend }
  return {
    plugins: [react(), tailwindcss()],
    define: { __BACKEND_URL__: JSON.stringify(backend) },
    server: { port, strictPort: true, host: '127.0.0.1', proxy },
    preview: { port, strictPort: true, host: '127.0.0.1', proxy },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (/node_modules[\/]three/.test(id)) return 'three'
            if (/node_modules[\/](recharts|d3-|victory-vendor)/.test(id)) return 'charts'
            if (/node_modules[\/](framer-motion|motion-|gsap)/.test(id)) return 'motion'
            return undefined
          },
        },
      },
    },
  }
})

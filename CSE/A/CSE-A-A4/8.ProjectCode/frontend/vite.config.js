import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from ../.env (BACKEND_PORT / FRONTEND_PORT) so run.bat and Vite agree.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8304'
  const frontend = Number(env.FRONTEND_PORT || 5304)
  const proxy = { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: true } }
  return {
    plugins: [react()],
    server: { port: frontend, strictPort: true, proxy },
    preview: { port: frontend, strictPort: true, proxy },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (/recharts|d3-|victory-vendor/.test(id)) return 'charts'
            if (/framer-motion|motion-dom|gsap|lenis/.test(id)) return 'motion'
            if (/react-dom|react-router|\/react\//.test(id)) return 'vendor'
            return undefined
          },
        },
      },
    },
  }
})

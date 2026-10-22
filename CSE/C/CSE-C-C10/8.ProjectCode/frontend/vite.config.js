import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Ports come from the project-root .env (FRONTEND_PORT / BACKEND_PORT)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8410'
  const port = Number(env.FRONTEND_PORT || 5410)
  const target = `http://127.0.0.1:${backend}`
  // The SPA routes live under /app so POST /predict can be proxied to FastAPI unchanged.
  const proxy = { '/api': { target, changeOrigin: true }, '/predict': { target, changeOrigin: true } }
  return {
    plugins: [react(), tailwindcss()],
    server: { port, strictPort: true, host: '127.0.0.1', proxy },
    preview: { port, strictPort: true, host: '127.0.0.1', proxy },
    build: {
      // three.js is its own lazy chunk, loaded only for the background grid
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return
            if (/[\\/]three[\\/]/.test(id)) return 'vendor-three'
            if (/recharts|[\\/]d3-|victory-vendor|decimal\.js|redux|immer|reselect/.test(id)) return 'vendor-charts'
            if (/framer-motion|motion-dom|motion-utils|[\\/]gsap[\\/]|[\\/]lenis[\\/]/.test(id)) return 'vendor-motion'
            if (/[\\/](react|react-dom|react-router|react-router-dom|scheduler|@remix-run)[\\/]/.test(id)) return 'vendor-react'
          },
        },
      },
    },
  }
})

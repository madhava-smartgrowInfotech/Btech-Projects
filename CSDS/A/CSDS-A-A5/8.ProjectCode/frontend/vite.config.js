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
    build: {
      // three.js (~510 kB) is its own lazy chunk, loaded only for the background grid
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return
            if (/[\\/]three[\\/]/.test(id)) return 'vendor-three'
            if (/force-graph|d3-force|kapsule|canvas-color-tracker|bezier-js|float-tooltip/.test(id)) return 'vendor-graph'
            if (/recharts|[\\/]d3-|victory-vendor|decimal\.js|redux|immer|reselect/.test(id)) return 'vendor-charts'
            if (/framer-motion|motion-dom|motion-utils|[\\/]gsap[\\/]|[\\/]lenis[\\/]/.test(id)) return 'vendor-motion'
            if (/[\\/](react|react-dom|react-router|react-router-dom|scheduler|@remix-run)[\\/]/.test(id)) return 'vendor-react'
          },
        },
      },
    },
  }
})

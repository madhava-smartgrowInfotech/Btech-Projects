import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from the project-level .env (BACKEND_PORT / FRONTEND_PORT).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = `http://localhost:${env.BACKEND_PORT || 8312}`
  const port = Number(env.FRONTEND_PORT || 5312)
  const proxy = { '/api': { target: backend, changeOrigin: true } }
  return {
    plugins: [react()],
    server: { port, strictPort: true, proxy },
    preview: { port, strictPort: true, proxy },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (id.includes('recharts') || id.includes('d3-') || id.includes('victory-vendor')) return 'charts'
            if (id.includes('gsap') || id.includes('lenis')) return 'motion'
            if (id.includes('framer-motion') || id.includes('/motion-')) return 'framer'
            if (id.includes('react-router')) return 'router'
            return undefined
          },
        },
      },
    },
  }
})

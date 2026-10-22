import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// The backend URL comes from VITE_API_URL (see ../.env); the dev server always listens on 5408.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', ['VITE_', 'FRONTEND_'])
  return {
    envDir: '..',
    plugins: [react()],
    server: { host: '127.0.0.1', port: Number(env.FRONTEND_PORT || 5408), strictPort: true },
    preview: { host: '127.0.0.1', port: Number(env.FRONTEND_PORT || 5408), strictPort: true },
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (/three|@react-three/.test(id)) return 'three'
            if (/recharts|d3-|victory/.test(id)) return 'charts'
            if (/framer-motion|motion-dom|gsap|lenis/.test(id)) return 'motion'
            return undefined
          },
        },
      },
    },
  }
})

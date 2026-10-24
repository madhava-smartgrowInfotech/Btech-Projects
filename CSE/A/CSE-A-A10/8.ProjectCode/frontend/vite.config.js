import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// Ports come from the project-level .env (backend 8310, frontend 5310); same defaults if it is missing.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = Number(env.BACKEND_PORT || 8310)
  const frontend = Number(env.FRONTEND_PORT || 5310)
  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: frontend,
      strictPort: true,
      host: 'localhost',
      proxy: { '/api': { target: `http://localhost:${backend}`, changeOrigin: true } },
    },
    preview: { port: frontend, strictPort: true, proxy: { '/api': { target: `http://localhost:${backend}`, changeOrigin: true } } },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (id.includes('three')) return 'three'
            if (id.includes('recharts') || id.includes('d3-') || id.includes('victory')) return 'charts'
            if (id.includes('framer-motion') || id.includes('gsap') || id.includes('lenis')) return 'motion'
            return 'vendor'
          },
        },
      },
    },
  }
})

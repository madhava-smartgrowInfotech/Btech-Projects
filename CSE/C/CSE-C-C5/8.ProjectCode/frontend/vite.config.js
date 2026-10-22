import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Ports come from the project-root .env (BACKEND_PORT / FRONTEND_PORT); defaults match the assigned 8405 / 5405.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8405'
  const port = Number(env.FRONTEND_PORT || 5405)
  return {
    plugins: [react(), tailwindcss()],
    server: { port, strictPort: true, host: true, proxy: { '/api': `http://localhost:${backend}` } },
    preview: { port, strictPort: true, proxy: { '/api': `http://localhost:${backend}` } },
    build: {
      chunkSizeWarningLimit: 700,
      rolldownOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/three')) return 'three'
            if (id.includes('node_modules/recharts') || id.includes('node_modules/d3-') || id.includes('node_modules/victory-vendor')) return 'charts'
            if (id.includes('node_modules/framer-motion') || id.includes('node_modules/motion-')) return 'motion'
            if (id.includes('node_modules/gsap')) return 'gsap'
          },
        },
      },
    },
  }
})

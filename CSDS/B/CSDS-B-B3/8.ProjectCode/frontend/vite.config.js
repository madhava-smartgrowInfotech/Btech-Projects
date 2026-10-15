import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Ports come from the project's root .env (BACKEND_PORT / FRONTEND_PORT); defaults match the batch assignment.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8203'
  const port = Number(env.FRONTEND_PORT || 5203)
  const proxy = { '/api': { target: `http://127.0.0.1:${backend}`, changeOrigin: true } }
  return {
    plugins: [react()],
    server: { port, strictPort: true, proxy },
    preview: { port, strictPort: true, proxy },
    build: {
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          // keep the heavy 3D and chart libraries out of the main bundle
          manualChunks(id) {
            if (id.includes('node_modules/three') || id.includes('@react-three')) return 'three'
            if (id.includes('node_modules/recharts') || id.includes('node_modules/d3-')) return 'charts'
            return undefined
          },
        },
      },
    },
  }
})

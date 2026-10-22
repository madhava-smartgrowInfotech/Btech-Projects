import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server on 5413; /api is proxied to the FastAPI backend (8413) so no CORS setup is needed.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = `http://127.0.0.1:${env.APP_PORT || 8413}`
  return {
    plugins: [react()],
    server: { port: Number(env.FRONTEND_PORT || 5413), strictPort: true, host: '127.0.0.1', proxy: { '/api': backend } },
    preview: { port: Number(env.FRONTEND_PORT || 5413), strictPort: true, host: '127.0.0.1', proxy: { '/api': backend } },
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
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

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = env.BACKEND_PORT || '8208'
  const port = Number(env.FRONTEND_PORT || 5208)
  return {
    plugins: [react()],
    server: {
      port,
      strictPort: true,
      proxy: { '/api': `http://127.0.0.1:${backend}` },
    },
    preview: { port, strictPort: true, proxy: { '/api': `http://127.0.0.1:${backend}` } },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            three: ['three', '@react-three/fiber', '@react-three/drei'],
            charts: ['recharts'],
          },
        },
      },
      chunkSizeWarningLimit: 1300,
    },
  }
})

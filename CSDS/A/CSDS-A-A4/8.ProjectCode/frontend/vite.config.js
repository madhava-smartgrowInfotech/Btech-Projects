import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const api = `http://127.0.0.1:${process.env.BACKEND_PORT || 8104}`

export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.FRONTEND_PORT || 5104),
    strictPort: true,
    proxy: { '/api': { target: api, changeOrigin: true } },
  },
  preview: { port: 5104, proxy: { '/api': { target: api, changeOrigin: true } } },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          motion: ['framer-motion'],
          charts: ['recharts'],
          gsap: ['gsap', 'lenis'],
        },
      },
    },
  },
})

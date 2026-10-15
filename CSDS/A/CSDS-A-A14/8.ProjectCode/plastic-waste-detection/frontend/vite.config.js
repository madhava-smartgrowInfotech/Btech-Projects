import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Ports: frontend 5114, backend 8114 (see ../.env.example)
const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:8114'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5114,
    strictPort: true,
    proxy: { '/api': { target: BACKEND, changeOrigin: true } },
  },
  preview: {
    port: 5114,
    strictPort: true,
    proxy: { '/api': { target: BACKEND, changeOrigin: true } },
  },
  build: { chunkSizeWarningLimit: 800 },
})

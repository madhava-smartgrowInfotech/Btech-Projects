import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API = 'http://127.0.0.1:8403'

export default defineConfig({
  plugins: [react()],
  server: { host: '127.0.0.1', port: 5403, strictPort: true, proxy: { '/api': { target: API, changeOrigin: true } } },
  preview: { host: '127.0.0.1', port: 5403, strictPort: true, proxy: { '/api': { target: API, changeOrigin: true } } },
  build: { chunkSizeWarningLimit: 1200 },
})

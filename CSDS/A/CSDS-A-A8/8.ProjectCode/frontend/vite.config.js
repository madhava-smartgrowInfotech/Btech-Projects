import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // the three.js hero scene is lazy-loaded, so its chunk is allowed to be large
  build: { chunkSizeWarningLimit: 900 },
  server: {
    port: 5108,
    strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8108' },
  },
})

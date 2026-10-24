import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5307,
    strictPort: true,
    proxy: { '/api': 'http://localhost:8307' },
  },
  preview: { port: 5307, strictPort: true, proxy: { '/api': 'http://localhost:8307' } },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('recharts') || id.includes('d3-') || id.includes('victory')) return 'charts'
          if (id.includes('gsap') || id.includes('lenis')) return 'motion'
          if (id.includes('framer-motion')) return 'framer'
          return 'vendor'
        },
      },
    },
  },
})

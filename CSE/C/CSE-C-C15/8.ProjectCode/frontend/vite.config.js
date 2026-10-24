import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const here = path.dirname(fileURLToPath(import.meta.url))

// Read BACKEND_PORT / FRONTEND_PORT from the project .env (one folder up).
function readEnv() {
  const out = {}
  try {
    for (const line of fs.readFileSync(path.join(here, '..', '.env'), 'utf8').split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/)
      if (m) out[m[1]] = m[2]
    }
  } catch { /* .env is optional */ }
  return out
}
const env = readEnv()
const backend = `http://127.0.0.1:${env.BACKEND_PORT || 8415}`

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    port: Number(env.FRONTEND_PORT || 5415),
    strictPort: true,
    proxy: {
      '/api': backend,
      '/static/results': backend,
    },
  },
  preview: {
    host: '127.0.0.1',
    port: Number(env.FRONTEND_PORT || 5415),
    strictPort: true,
    proxy: { '/api': backend, '/static/results': backend },
  },
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('/three/')) return 'three'
          if (id.includes('recharts') || id.includes('/d3-') || id.includes('victory-vendor')) return 'charts'
          if (id.includes('framer-motion') || id.includes('/motion')) return 'motion'
          if (id.includes('gsap') || id.includes('lenis')) return 'gsap'
          return undefined
        },
      },
    },
  },
})

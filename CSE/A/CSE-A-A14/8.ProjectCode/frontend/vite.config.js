import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))

// Ports come from the project's .env (8.ProjectCode/.env) so run.bat, the API and Vite agree.
function readEnv() {
  const out = {}
  try {
    for (const line of fs.readFileSync(path.resolve(here, '../.env'), 'utf8').split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/)
      if (m && !line.trim().startsWith('#')) out[m[1]] = m[2]
    }
  } catch {
    /* no .env: fall back to defaults */
  }
  return out
}

const env = readEnv()
const frontPort = Number(env.FRONTEND_PORT || 5314)
const backPort = Number(env.BACKEND_PORT || 8314)
const proxy = { '/api': { target: `http://127.0.0.1:${backPort}`, changeOrigin: true } }

export default defineConfig({
  plugins: [react()],
  server: { port: frontPort, strictPort: true, host: 'localhost', proxy },
  preview: { port: frontPort, strictPort: true, host: 'localhost', proxy },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (/recharts|d3-|victory-vendor|decimal\.js-light|internmap/.test(id)) return 'vendor-charts'
          if (/framer-motion|motion-dom|motion-utils/.test(id)) return 'motion'
          if (/gsap|lenis|canvas-confetti/.test(id)) return 'fx'
          if (/react-router/.test(id)) return 'router'
          return undefined
        },
      },
    },
  },
})


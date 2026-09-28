import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const backend = `http://127.0.0.1:${env.BACKEND_PORT || 8215}`
  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: Number(env.FRONTEND_PORT || 5215),
      strictPort: true,
      host: true,
      allowedHosts: ['.trycloudflare.com', 'localhost'],
      // behind the Cloudflare tunnel the page is https on 443, so live-reload must use wss:443
      hmr: process.env.MEDIQUEUE_TUNNEL ? { protocol: 'wss', clientPort: 443 } : undefined,
      proxy: { '/api': { target: backend, changeOrigin: true, ws: true } },
    },
    build: { chunkSizeWarningLimit: 800 },
    preview: { port: Number(env.FRONTEND_PORT || 5215), strictPort: true },
  }
})

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const BACKEND_PORT = process.env.BACKEND_PORT || 8107;
const FRONTEND_PORT = Number(process.env.FRONTEND_PORT || 5107);

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "SHEGUARD",
        short_name: "SHEGUARD",
        description: "Women's safety companion - safe routes, SOS, live tracking, evidence.",
        theme_color: "#9d174d",
        background_color: "#0f172a",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "/favicon.svg", sizes: "192x192", type: "image/svg+xml", purpose: "any" },
          { src: "/favicon.svg", sizes: "512x512", type: "image/svg+xml", purpose: "any" },
        ],
      },
    }),
  ],
  server: {
    host: true,
    port: FRONTEND_PORT,
    strictPort: true,
    // Allow the Cloudflare quick-tunnel hostname to reach this dev server.
    allowedHosts: [".trycloudflare.com", "localhost"],
    proxy: {
      "/api": {
        target: `http://localhost:${BACKEND_PORT}`,
        changeOrigin: true,
      },
      "/ws": {
        target: `ws://localhost:${BACKEND_PORT}`,
        ws: true,
      },
      "/evidence-files": {
        target: `http://localhost:${BACKEND_PORT}`,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: true,
    port: FRONTEND_PORT,
    strictPort: true,
  },
});

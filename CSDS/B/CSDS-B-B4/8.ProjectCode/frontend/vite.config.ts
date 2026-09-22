import path from "node:path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Ports live in the project's root .env so they can be changed in one place.
// UPI Guardian always uses 5204 (web) and 8204 (API) so it can run next to other products.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, ".."), "");
  const webPort = Number(env.FRONTEND_PORT || 5204);
  const apiPort = Number(env.API_PORT || 8204);
  const apiTarget = `http://127.0.0.1:${apiPort}`;

  const proxy = {
    "/api": { target: apiTarget, changeOrigin: true, ws: true },
    "/docs": { target: apiTarget, changeOrigin: true },
    "/openapi.json": { target: apiTarget, changeOrigin: true },
  };

  return {
    plugins: [
      react(),
      VitePWA({
        registerType: "autoUpdate",
        includeAssets: ["favicon.svg", "apple-touch-icon.png"],
        manifest: {
          name: "UPI Guardian",
          short_name: "UPI Guardian",
          description: "Stops UPI fraud before the money leaves.",
          theme_color: "#0f766e",
          background_color: "#0b1215",
          display: "standalone",
          orientation: "portrait",
          start_url: "/app",
          scope: "/",
          lang: "en",
          categories: ["finance", "security"],
          icons: [
            { src: "pwa-192.png", sizes: "192x192", type: "image/png" },
            { src: "pwa-512.png", sizes: "512x512", type: "image/png" },
            { src: "pwa-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
          ],
        },
        workbox: {
          navigateFallback: "/index.html",
          navigateFallbackDenylist: [/^\/api/, /^\/docs/, /^\/openapi\.json/],
          globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
          maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
          runtimeCaching: [
            {
              urlPattern: ({ url }) => url.origin === "https://fonts.googleapis.com" || url.origin === "https://fonts.gstatic.com",
              handler: "CacheFirst",
              options: { cacheName: "google-fonts", expiration: { maxEntries: 30, maxAgeSeconds: 60 * 60 * 24 * 365 } },
            },
            {
              urlPattern: ({ url }) => url.pathname.startsWith("/api/voice/audio/"),
              handler: "CacheFirst",
              options: { cacheName: "voice-audio", expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 } },
            },
          ],
        },
        devOptions: { enabled: false },
      }),
    ],
    resolve: {
      alias: { "@": path.resolve(__dirname, "src") },
    },
    server: {
      host: true,
      port: webPort,
      strictPort: true,
      allowedHosts: [".trycloudflare.com", "localhost", "127.0.0.1"],
      proxy,
    },
    preview: {
      host: true,
      port: webPort,
      strictPort: true,
      allowedHosts: [".trycloudflare.com", "localhost", "127.0.0.1"],
      proxy,
    },
    build: {
      chunkSizeWarningLimit: 1600,
    },
  };
});

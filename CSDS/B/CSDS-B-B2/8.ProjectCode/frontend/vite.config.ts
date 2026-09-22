import path from "node:path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Ports come from the project's .env (one level up). Fixed ports - other products may run on this PC.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(import.meta.dirname, ".."), "");
  const frontendPort = Number(env.FRONTEND_PORT || 5202);
  const backendPort = Number(env.BACKEND_PORT || 8202);
  const api = { "/api": { target: `http://127.0.0.1:${backendPort}`, changeOrigin: false } };

  return {
    plugins: [
      react(),
      VitePWA({
        strategies: "injectManifest",
        srcDir: "src",
        filename: "sw.ts",
        registerType: "autoUpdate",
        injectRegister: false,
        injectManifest: { globPatterns: ["**/*.{js,css,html,svg,png,woff2}"], maximumFileSizeToCacheInBytes: 4 * 1024 * 1024 },
        devOptions: { enabled: false },
        manifest: {
          name: "SignalScout",
          short_name: "SignalScout",
          description: "Measure mobile coverage, find better signal and file complaints with evidence.",
          start_url: "/probe",
          scope: "/",
          display: "standalone",
          orientation: "portrait",
          background_color: "#0d1017",
          theme_color: "#3d5afe",
          icons: [
            { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
            { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
            { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
          ],
          shortcuts: [
            { name: "Field probe", url: "/probe" },
            { name: "Coverage map", url: "/app/map" },
          ],
        },
      }),
    ],
    envDir: path.resolve(import.meta.dirname, ".."),
    envPrefix: "VITE_",
    resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
    server: {
      port: frontendPort,
      strictPort: true,
      host: true,
      allowedHosts: [".trycloudflare.com"],
      proxy: api,
    },
    preview: { port: frontendPort, strictPort: true, host: true, proxy: api },
    build: { outDir: "dist", sourcemap: false, chunkSizeWarningLimit: 1200 },
  };
});

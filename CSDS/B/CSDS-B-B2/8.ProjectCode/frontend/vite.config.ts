import path from "node:path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Ports come from the project's .env (one level up). Fixed ports - other products may run on this PC.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(import.meta.dirname, ".."), "");
  const frontendPort = Number(env.FRONTEND_PORT || 5202);
  const backendPort = Number(env.BACKEND_PORT || 8202);
  const api = { "/api": { target: `http://127.0.0.1:${backendPort}`, changeOrigin: false } };

  return {
    plugins: [react()],
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

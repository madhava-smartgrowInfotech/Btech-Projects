import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  // ports come from the project's .env (one level up): FRONTEND_PORT / BACKEND_PORT
  const env = loadEnv(mode, path.resolve(import.meta.dirname, ".."), "");
  const frontend = Number(env.FRONTEND_PORT || 5301);
  const backend = Number(env.BACKEND_PORT || 8301);
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
    server: {
      port: frontend,
      strictPort: true,
      proxy: { "/api": { target: `http://127.0.0.1:${backend}`, changeOrigin: true } },
    },
    preview: { port: frontend, strictPort: true, proxy: { "/api": { target: `http://127.0.0.1:${backend}`, changeOrigin: true } } },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id: string) {
            if (!id.includes("node_modules")) return undefined;
            if (/node_modules[\/](recharts|d3-|victory-vendor)/.test(id)) return "charts";
            if (/node_modules[\/](framer-motion|motion-dom|motion-utils|gsap|lenis)/.test(id)) return "motion";
            return undefined;
          },
        },
      },
    },
  };
});

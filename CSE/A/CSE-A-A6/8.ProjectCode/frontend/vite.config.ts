import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Ports are fixed for Smart Rider (other products may run on the same PC).
// They are read from the project-root .env so both servers agree.
export default defineConfig(({ mode }) => {
  const rootDir = path.resolve(__dirname, "..");
  const env = loadEnv(mode, rootDir, "");
  const frontendPort = Number(env.FRONTEND_PORT || 5306);
  const backendPort = Number(env.BACKEND_PORT || 8306);
  const backendUrl = `http://127.0.0.1:${backendPort}`;
  const proxy = { "/api": { target: backendUrl, changeOrigin: true }, "/docs": backendUrl, "/openapi.json": backendUrl };

  return {
    envDir: rootDir,
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": path.resolve(__dirname, "src") } },
    server: { host: "127.0.0.1", port: frontendPort, strictPort: true, proxy },
    preview: { host: "127.0.0.1", port: frontendPort, strictPort: true, proxy },
    build: {
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          manualChunks(id: string) {
            if (!id.includes("node_modules")) return undefined;
            if (/node_modules[\/](recharts|d3-|victory-vendor)/.test(id)) return "charts";
            if (/node_modules[\/](framer-motion|motion-|gsap|lenis)/.test(id)) return "motion";
            return undefined;
          },
        },
      },
    },
  };
});

import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Ports are fixed for PolicyLens (other products may run on the same PC).
// They are read from the project-root .env so both servers agree.
export default defineConfig(({ mode }) => {
  const rootDir = path.resolve(__dirname, "..");
  const env = loadEnv(mode, rootDir, "");
  const frontendPort = Number(env.FRONTEND_PORT || 5101);
  const backendPort = Number(env.BACKEND_PORT || 8101);
  const backendUrl = `http://127.0.0.1:${backendPort}`;

  return {
    envDir: rootDir,
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: { "@": path.resolve(__dirname, "src") },
    },
    server: {
      host: true,
      port: frontendPort,
      strictPort: true,
      proxy: {
        "/api": { target: backendUrl, changeOrigin: true },
      },
    },
    preview: {
      host: true,
      port: frontendPort,
      strictPort: true,
      proxy: {
        "/api": { target: backendUrl, changeOrigin: true },
      },
    },
    build: {
      chunkSizeWarningLimit: 1200,
    },
  };
});

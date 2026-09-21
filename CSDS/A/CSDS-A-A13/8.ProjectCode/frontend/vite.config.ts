import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Ports come from the root .env (API_PORT / WEB_PORT). They are fixed so SeatWise
// can run next to other products on the same machine: never fall back to 5173.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, ".."), "");
  const webPort = Number(env.WEB_PORT || 5113);
  const apiPort = Number(env.API_PORT || 8113);

  return {
    plugins: [react()],
    resolve: {
      alias: { "@": path.resolve(__dirname, "src") },
    },
    server: {
      port: webPort,
      strictPort: true,
      host: true, // reachable from tablets and phones on the same network
      proxy: {
        "/api": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: true },
      },
    },
    preview: {
      port: webPort,
      strictPort: true,
      host: true,
      proxy: {
        "/api": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: true },
      },
    },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ["react", "react-dom", "react-router-dom"],
            charts: ["recharts"],
            motion: ["motion", "gsap", "lenis"],
          },
        },
      },
    },
  };
});

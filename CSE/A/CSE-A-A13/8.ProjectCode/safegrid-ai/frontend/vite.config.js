import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const root = path.dirname(fileURLToPath(import.meta.url));

// Ports come from the project-level .env (BACKEND_PORT / FRONTEND_PORT); defaults match the batch allocation.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(root, ".."), "");
  const backend = env.BACKEND_PORT || "8313";
  const frontend = Number(env.FRONTEND_PORT || 5313);
  return {
    plugins: [react()],
    server: {
      port: frontend,
      strictPort: true,
      host: "127.0.0.1",
      proxy: {
        "/api": `http://127.0.0.1:${backend}`,
        "/ws": { target: `ws://127.0.0.1:${backend}`, ws: true },
      },
    },
    preview: { port: frontend, strictPort: true, host: "127.0.0.1" },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks: {
            three: ["three", "@react-three/fiber", "@react-three/drei"],
            charts: ["recharts"],
            motion: ["framer-motion", "gsap", "lenis"],
          },
        },
      },
    },
  };
});

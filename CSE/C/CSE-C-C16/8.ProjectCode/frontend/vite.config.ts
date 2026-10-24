import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Ports are fixed for this product (other products may run on the same PC).
// They are read from the project-root .env so both servers agree.
export default defineConfig(({ mode }) => {
  const rootDir = path.resolve(__dirname, "..");
  const env = loadEnv(mode, rootDir, "");
  const frontendPort = Number(env.FRONTEND_PORT || 5416);
  const backendPort = Number(env.BACKEND_PORT || 8416);
  const backendUrl = `http://127.0.0.1:${backendPort}`;

  return {
    envDir: rootDir,
    plugins: [react(), tailwindcss()],
    // Pre-bundle everything at start-up so lazy routes (landing, charts) never trigger a re-optimise + page reload.
    optimizeDeps: {
      include: [
        "react", "react-dom", "react-dom/client", "react-router", "react-is", "axios", "framer-motion", "gsap", "gsap/ScrollTrigger",
        "lenis", "lucide-react", "radix-ui", "recharts", "sonner", "clsx", "tailwind-merge", "class-variance-authority",
        "@tanstack/react-query",
      ],
    },
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

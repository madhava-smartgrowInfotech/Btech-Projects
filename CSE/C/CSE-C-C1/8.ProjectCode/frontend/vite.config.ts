import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Ports are fixed for AegisBallot (other products may run on the same PC).
// They are read from the project-root .env so both servers agree.
export default defineConfig(({ mode }) => {
  const rootDir = path.resolve(__dirname, "..");
  const env = loadEnv(mode, rootDir, "");
  const frontendPort = Number(env.FRONTEND_PORT || 5401);
  const backendPort = Number(env.BACKEND_PORT || 8401);
  const backendUrl = `http://127.0.0.1:${backendPort}`;
  const proxy = { "/api": { target: backendUrl, changeOrigin: true } };

  return {
    // Only FRONTEND_/BACKEND_ ports are needed here; never expose the root .env secrets to the browser bundle.
    envDir: rootDir,
    envPrefix: "VITE_",
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": path.resolve(__dirname, "src") } },
    server: { host: true, port: frontendPort, strictPort: true, proxy },
    preview: { host: true, port: frontendPort, strictPort: true, proxy },
    build: {
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          manualChunks(id: string) {
            if (!id.includes("node_modules")) return undefined;
            if (id.includes("recharts") || id.includes("d3-")) return "charts";
            if (id.includes("framer-motion") || id.includes("gsap") || id.includes("lenis")) return "motion";
            if (id.includes("radix-ui") || id.includes("@radix-ui")) return "radix";
            return "vendor";
          },
        },
      },
    },
  };
});

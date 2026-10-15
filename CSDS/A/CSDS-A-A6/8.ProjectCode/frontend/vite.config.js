import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ mode }) => {
  // The ports live in the project-root .env (one level up), which Vite does not read by default.
  const rootEnv = loadEnv(mode, fileURLToPath(new URL("..", import.meta.url)), "");
  const BACKEND_PORT = Number(rootEnv.BACKEND_PORT || process.env.BACKEND_PORT || 8106);
  const FRONTEND_PORT = Number(rootEnv.FRONTEND_PORT || process.env.FRONTEND_PORT || 5106);

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      port: FRONTEND_PORT,
      strictPort: true,
      proxy: {
        "/api": {
          target: `http://127.0.0.1:${BACKEND_PORT}`,
          changeOrigin: true,
        },
      },
    },
  };
});

import { readFileSync } from "node:fs";
import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Ports come from the project's .env so run.bat, the API CORS list and Vite always agree.
function readEnv() {
  const out: Record<string, string> = {};
  try {
    for (const line of readFileSync(path.resolve(__dirname, "../.env"), "utf8").split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Z_]+)\s*=\s*(.*)\s*$/);
      if (m) out[m[1]] = m[2];
    }
  } catch {
    /* .env missing: fall back to the defaults below */
  }
  return out;
}
const env = readEnv();
const backend = Number(env.BACKEND_PORT ?? 8311);
const frontend = Number(env.FRONTEND_PORT ?? 5311);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: { host: "127.0.0.1", port: frontend, strictPort: true, proxy: { "/api": `http://127.0.0.1:${backend}` } },
  preview: { host: "127.0.0.1", port: frontend, strictPort: true, proxy: { "/api": `http://127.0.0.1:${backend}` } },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("recharts") || id.includes("d3-") || id.includes("victory")) return "charts";
          if (id.includes("gsap") || id.includes("lenis")) return "scroll";
          if (id.includes("framer-motion") || id.includes("motion-")) return "motion";
          if (id.includes("react-markdown") || id.includes("remark") || id.includes("rehype") || id.includes("unified") || id.includes("micromark") || id.includes("mdast") || id.includes("hast")) return "markdown";
          return undefined;
        },
      },
    },
  },
});

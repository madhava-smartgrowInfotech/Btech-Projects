import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { createAsyncStoragePersister } from "@tanstack/query-async-storage-persister";
import { createStore, del, get, set } from "idb-keyval";
import { MotionConfig } from "motion/react";
import { registerSW } from "virtual:pwa-register";
import "@fontsource-variable/inter";
import "@fontsource-variable/space-grotesk";
import "@fontsource-variable/jetbrains-mono";
import "./index.css";
import App from "./App";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/lib/theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 15_000, gcTime: 24 * 3600_000, refetchOnWindowFocus: false, retry: 1 },
    mutations: { retry: 0 },
  },
});

// Offline-first dashboard: the last data you loaded is kept in IndexedDB and shown when the connection drops.
const cacheStore = createStore("signalscout-cache", "queries");
const persister = createAsyncStoragePersister({
  storage: { getItem: (k) => get<string>(k, cacheStore).then((v) => v ?? null), setItem: (k, v) => set(k, v, cacheStore), removeItem: (k) => del(k, cacheStore) },
  throttleTime: 2000,
});

if ("serviceWorker" in navigator && import.meta.env.PROD) registerSW({ immediate: true });

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{
        persister,
        maxAge: 24 * 3600_000,
        buster: "1.0.0",
        dehydrateOptions: { shouldDehydrateQuery: (q) => q.state.status === "success" && q.queryKey[0] !== "coverage-heat" },
      }}
    >
      <ThemeProvider>
        <MotionConfig reducedMotion="user">
          <TooltipProvider delayDuration={200}>
            <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
              <AuthProvider>
                <App />
                <Toaster />
              </AuthProvider>
            </BrowserRouter>
          </TooltipProvider>
        </MotionConfig>
      </ThemeProvider>
    </PersistQueryClientProvider>
  </React.StrictMode>,
);

import "@/index.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import { App } from "@/App";
import { Toaster } from "@/components/ui/Toast";
import { TooltipProvider } from "@/components/ui/Popups";
import { AuthProvider } from "@/lib/auth";
import { SettingsProvider } from "@/lib/settings";
import { ThemeProvider } from "@/lib/theme";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <SettingsProvider>
          <AuthProvider>
            <TooltipProvider delayDuration={250}>
              <BrowserRouter>
                <App />
              </BrowserRouter>
              <Toaster />
            </TooltipProvider>
          </AuthProvider>
        </SettingsProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);

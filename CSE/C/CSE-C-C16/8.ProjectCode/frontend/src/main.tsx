import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "framer-motion";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import App from "@/App";
import { TooltipProvider } from "@/components/ui/Popups";
import { Toaster } from "@/components/ui/Toast";
import { AuthProvider } from "@/lib/auth";
import { LangProvider } from "@/lib/i18n";
import { ThemeProvider } from "@/lib/theme";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <LangProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <TooltipProvider delayDuration={200}>
              <MotionConfig reducedMotion="user">
                <BrowserRouter>
                  <App />
                </BrowserRouter>
                <Toaster />
              </MotionConfig>
            </TooltipProvider>
          </AuthProvider>
        </QueryClientProvider>
      </LangProvider>
    </ThemeProvider>
  </StrictMode>,
);

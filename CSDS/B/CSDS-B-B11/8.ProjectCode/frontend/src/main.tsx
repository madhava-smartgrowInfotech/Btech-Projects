import "./index.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "framer-motion";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import App from "@/App";
import { TooltipProvider } from "@/components/ui/Popups";
import { Toaster } from "@/components/ui/Toast";
import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/lib/theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* "user": honour the OS reduced-motion setting for every motion component */}
    <MotionConfig reducedMotion="user">
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <TooltipProvider delayDuration={200}>
              <BrowserRouter>
                <App />
              </BrowserRouter>
              <Toaster />
            </TooltipProvider>
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </MotionConfig>
  </StrictMode>,
);

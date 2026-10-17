import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import "./index.css";
import App from "./App";
import { TooltipProvider } from "@/components/ui/Popups";
import { Toaster } from "@/components/ui/Toast";
import { api, isUnauthorized } from "@/lib/api";
import { AuthProvider } from "@/lib/auth";
import { keys } from "@/lib/queries";
import { ThemeProvider } from "@/lib/theme";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
});

// A 401 from any protected call means the session ended: drop the user so the route guard sends them to sign in.
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url: string = error?.config?.url ?? "";
    if (isUnauthorized(error) && !url.startsWith("/auth/")) queryClient.setQueryData(keys.me, null);
    return Promise.reject(error);
  },
);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider delayDuration={200}>
          <AuthProvider>
            <BrowserRouter>
              <App />
            </BrowserRouter>
            <Toaster />
          </AuthProvider>
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
);

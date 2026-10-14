import { QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense, type ReactNode } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader, Toaster } from "@/components/ui/Feedback";
import { TooltipProvider } from "@/components/ui/Popups";
import { AuthProvider, HOME, type Role, useAuth } from "@/lib/auth";
import { queryClient } from "@/lib/queries";
import { ThemeProvider } from "@/lib/theme";
import AuditPage from "@/pages/AuditPage";
import DoctorPage from "@/pages/DoctorPage";
import HospitalConsole from "@/pages/HospitalConsole";
import Login from "@/pages/Login";
import PatientPage from "@/pages/PatientPage";

// The landing page carries the motion and scroll libraries, so it loads on its own.
const Landing = lazy(() => import("@/pages/Landing"));

/** Sends signed-out visitors to sign-in, keeping the page they wanted. */
function RequireAuth() {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

/** Only the roles listed may open a screen; others go to their own home. */
function RoleGate({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return null;
  if (!roles.includes(user.role)) return <Navigate to={HOME[user.role]} replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <AuthProvider>
            <BrowserRouter>
              <Suspense fallback={<FullPageLoader />}>
                <Routes>
                  <Route path="/" element={<Landing />} />
                  <Route path="/login" element={<Login />} />
                  <Route element={<RequireAuth />}>
                    <Route element={<AppShell />}>
                      <Route
                        path="/patient"
                        element={
                          <RoleGate roles={["patient"]}>
                            <PatientPage />
                          </RoleGate>
                        }
                      />
                      <Route
                        path="/doctor"
                        element={
                          <RoleGate roles={["doctor"]}>
                            <DoctorPage />
                          </RoleGate>
                        }
                      />
                      <Route
                        path="/hospital"
                        element={
                          <RoleGate roles={["staff", "admin"]}>
                            <HospitalConsole />
                          </RoleGate>
                        }
                      />
                      <Route path="/audit" element={<AuditPage />} />
                    </Route>
                  </Route>
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </BrowserRouter>
            <Toaster />
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

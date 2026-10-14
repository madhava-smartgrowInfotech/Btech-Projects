import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router";

import { FullPageLoader } from "@/components/ui/Feedback";
import { AppShell } from "@/components/ui/AppShell";
import { useAuth } from "@/lib/auth";

// Each screen is its own chunk: charts (recharts), scroll motion (gsap, lenis) and the landing
// page only download when a visitor reaches them.
const Landing = lazy(() => import("@/pages/Landing"));
const AuthPage = lazy(() => import("@/pages/AuthPage"));
const ProfileWizard = lazy(() => import("@/pages/ProfileWizard"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const PlanPage = lazy(() => import("@/pages/PlanPage"));
const FoodLog = lazy(() => import("@/pages/FoodLog"));
const Progress = lazy(() => import("@/pages/Progress"));

/** Signed-out visitors go to the login screen. */
function RequireLogin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/** Signed-in users without a saved profile are sent to the profile wizard first. */
function RequireProfile() {
  const { user } = useAuth();
  if (user && !user.has_profile) return <Navigate to="/profile" replace />;
  return <Outlet />;
}

export default function App() {
  const { user } = useAuth();
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Landing />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />

        <Route
          element={
            <RequireLogin>
              <AppShell />
            </RequireLogin>
          }
        >
          <Route path="/profile" element={<ProfileWizard />} />
          <Route element={<RequireProfile />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/plan" element={<PlanPage />} />
            <Route path="/log" element={<FoodLog />} />
            <Route path="/progress" element={<Progress />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

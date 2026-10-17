import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";
import { useAuth } from "@/lib/auth";

const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const Register = lazy(() => import("@/pages/Register"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Upload = lazy(() => import("@/pages/Upload"));
const Documents = lazy(() => import("@/pages/Documents"));
const Ask = lazy(() => import("@/pages/Ask"));
const Quiz = lazy(() => import("@/pages/Quiz"));
const Roadmap = lazy(() => import("@/pages/Roadmap"));
const NotFound = lazy(() => import("@/pages/NotFound"));

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullPageLoader />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return <>{children}</>;
}

/** Sign in / register pages: once there is a user, move on (back to where they came from, or to a sensible first screen). */
function PublicOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullPageLoader />;
  if (user) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from ?? (location.pathname === "/register" ? "/app/upload" : "/app")} replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route
          path="/login"
          element={
            <PublicOnly>
              <Login />
            </PublicOnly>
          }
        />
        <Route
          path="/register"
          element={
            <PublicOnly>
              <Register />
            </PublicOnly>
          }
        />
        <Route
          path="/app"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="documents" element={<Documents />} />
          <Route path="ask" element={<Ask />} />
          <Route path="quiz" element={<Quiz />} />
          <Route path="roadmap" element={<Roadmap />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

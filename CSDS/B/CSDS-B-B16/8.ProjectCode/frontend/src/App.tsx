import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";
import { useAuth } from "@/lib/auth";

// Every screen is its own chunk, so recharts and gsap load only where they are used.
const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const NewScreening = lazy(() => import("@/pages/NewScreening"));
const Result = lazy(() => import("@/pages/Result"));
const Report = lazy(() => import("@/pages/Report"));
const Patients = lazy(() => import("@/pages/Patients"));
const PatientDetail = lazy(() => import("@/pages/PatientDetail"));
const Performance = lazy(() => import("@/pages/Performance"));

function RequireAuth({ children }: { children: ReactNode }) {
  const { signedIn } = useAuth();
  const location = useLocation();
  if (!signedIn) return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route path="/screening/new" element={<NewScreening />} />
          <Route path="/screenings/:id" element={<Result />} />
          <Route path="/screenings/:id/report" element={<Report />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/patients/:id" element={<PatientDetail />} />
          <Route path="/performance" element={<Performance />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

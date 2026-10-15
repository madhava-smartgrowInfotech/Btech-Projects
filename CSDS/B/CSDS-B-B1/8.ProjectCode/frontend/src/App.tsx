import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router";

import { FullPageLoader } from "@/components/ui/Feedback";
import { AppShell } from "@/components/ui/AppShell";
import { homeFor, useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

// Every screen is its own chunk, so the first paint only loads the shell it needs.
const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const FileComplaint = lazy(() => import("@/pages/FileComplaint"));
const Track = lazy(() => import("@/pages/Track"));
const Queue = lazy(() => import("@/pages/Queue"));
const ComplaintDetail = lazy(() => import("@/pages/ComplaintDetail"));
const Analytics = lazy(() => import("@/pages/Analytics"));

function Guard({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to={homeFor(user)} replace />;
  return <Suspense fallback={<FullPageLoader />}>{children}</Suspense>;
}

function ShellGate() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <AppShell />;
}

function AppHome() {
  const { user } = useAuth();
  return <Navigate to={homeFor(user)} replace />;
}

const CITIZEN: Role[] = ["citizen"];
const STAFF: Role[] = ["officer", "admin"];

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/app" element={<ShellGate />}>
        <Route index element={<AppHome />} />
        <Route path="file" element={<Guard roles={CITIZEN}><FileComplaint /></Guard>} />
        <Route path="track" element={<Guard roles={CITIZEN}><Track /></Guard>} />
        <Route path="track/:trackingId" element={<Guard roles={CITIZEN}><Track /></Guard>} />
        <Route path="queue" element={<Guard roles={STAFF}><Queue /></Guard>} />
        <Route path="complaints/:id" element={<Guard roles={STAFF}><ComplaintDetail /></Guard>} />
        <Route path="analytics" element={<Guard roles={STAFF}><Analytics /></Guard>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </Suspense>
  );
}

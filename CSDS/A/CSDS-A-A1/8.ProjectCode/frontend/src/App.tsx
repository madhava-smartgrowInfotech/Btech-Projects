import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";

import { AppLayout } from "@/components/layout/AppLayout";
import { FullPageLoader } from "@/components/common/States";
import { useAuth } from "@/lib/auth";

const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const Register = lazy(() => import("@/pages/Register"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Policies = lazy(() => import("@/pages/Policies"));
const PolicyView = lazy(() => import("@/pages/PolicyView"));
const Chat = lazy(() => import("@/pages/Chat"));
const ClaimCopilot = lazy(() => import("@/pages/ClaimCopilot"));
const Compare = lazy(() => import("@/pages/Compare"));
const ModelPerformance = lazy(() => import("@/pages/ModelPerformance"));
const Settings = lazy(() => import("@/pages/Settings"));
const NotFound = lazy(() => import("@/pages/NotFound"));

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullPageLoader />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return <>{children}</>;
}

function GuestOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <FullPageLoader />;
  if (user) return <Navigate to="/app" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
        <Route path="/register" element={<GuestOnly><Register /></GuestOnly>} />
        <Route
          path="/app"
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="policies" element={<Policies />} />
          <Route path="policies/:policyId" element={<PolicyView />} />
          <Route path="chat" element={<Chat />} />
          <Route path="chat/:conversationId" element={<Chat />} />
          <Route path="claims" element={<ClaimCopilot />} />
          <Route path="claims/:caseId" element={<ClaimCopilot />} />
          <Route path="compare" element={<Compare />} />
          <Route path="compare/:comparisonId" element={<Compare />} />
          <Route path="performance" element={<ModelPerformance />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

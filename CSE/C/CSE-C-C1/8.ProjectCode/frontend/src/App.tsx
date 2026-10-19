import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";
import { HOME_BY_ROLE, useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const NotFound = lazy(() => import("@/pages/NotFound"));
const Results = lazy(() => import("@/pages/Results"));
const AdminDashboard = lazy(() => import("@/pages/admin/Dashboard"));
const AdminElections = lazy(() => import("@/pages/admin/Elections"));
const AdminElectionDetail = lazy(() => import("@/pages/admin/ElectionDetail"));
const AdminBenchmarks = lazy(() => import("@/pages/admin/Benchmarks"));
const VoterElections = lazy(() => import("@/pages/voter/MyElections"));
const VoteFlow = lazy(() => import("@/pages/voter/VoteFlow"));
const AuditorDashboard = lazy(() => import("@/pages/auditor/Auditor"));
const BlockDetail = lazy(() => import("@/pages/auditor/BlockDetail"));

/** Sends signed-out visitors to /login (remembering where they were going) and wrong-role users to their own home. */
function Protected({ roles, children }: { roles?: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullPageLoader />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) return <Navigate to={HOME_BY_ROLE[user.role]} replace />;
  return <>{children}</>;
}

function RoleHome() {
  const { user } = useAuth();
  return <Navigate to={user ? HOME_BY_ROLE[user.role] : "/login"} replace />;
}

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/app"
          element={
            <Protected>
              <AppShell />
            </Protected>
          }
        >
          <Route index element={<RoleHome />} />
          <Route path="admin" element={<Protected roles={["ADMIN"]}><AdminDashboard /></Protected>} />
          <Route path="admin/elections" element={<Protected roles={["ADMIN"]}><AdminElections /></Protected>} />
          <Route path="admin/elections/:id" element={<Protected roles={["ADMIN"]}><AdminElectionDetail /></Protected>} />
          <Route path="admin/benchmarks" element={<Protected roles={["ADMIN"]}><AdminBenchmarks /></Protected>} />
          <Route path="results/:id" element={<Protected roles={["ADMIN", "VOTER"]}><Results /></Protected>} />
          <Route path="voter" element={<Protected roles={["VOTER"]}><VoterElections /></Protected>} />
          <Route path="voter/:id/verify" element={<Protected roles={["VOTER"]}><VoteFlow /></Protected>} />
          <Route path="auditor" element={<Protected roles={["AUDITOR"]}><AuditorDashboard /></Protected>} />
          <Route path="auditor/blocks/:index" element={<Protected roles={["AUDITOR"]}><BlockDetail /></Protected>} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  );
}

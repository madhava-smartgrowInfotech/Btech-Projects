import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";

import { ProtectedRoute } from "@/components/app/ProtectedRoute.jsx";
import { PublicShell } from "@/components/app/PublicShell.jsx";
import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";
import { Toaster } from "@/components/ui/Toast";
import ClauseDetail from "./pages/ClauseDetail.jsx";
import ContractList from "./pages/ContractList.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Upload from "./pages/Upload.jsx";

// Heavier pages (recharts, GSAP scroll effects) load on demand.
const Landing = lazy(() => import("./pages/Landing.jsx"));
const Evaluation = lazy(() => import("./pages/Evaluation.jsx"));
const ContractReport = lazy(() => import("./pages/ContractReport.jsx"));
const ClauseGraph = lazy(() => import("./pages/ClauseGraph.jsx"));

// The app used to live at /upload and /contracts. Keep old links working.
function LegacyContractRedirect() {
  const { pathname, search } = useLocation();
  return <Navigate to={`/app${pathname}${search}`} replace />;
}

export default function App() {
  return (
    <>
      <Suspense fallback={<FullPageLoader />}>
        <Routes>
          <Route element={<PublicShell />}>
            <Route index element={<Landing />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
            <Route path="evaluation" element={<Evaluation />} />
          </Route>

          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<ContractList />} />
            <Route path="upload" element={<Upload />} />
            <Route path="contracts/:id" element={<ContractReport />} />
            <Route path="contracts/:id/clauses/:clauseId" element={<ClauseDetail />} />
            <Route path="contracts/:id/graph" element={<ClauseGraph />} />
          </Route>

          <Route path="/upload" element={<Navigate to="/app/upload" replace />} />
          <Route path="/contracts" element={<Navigate to="/app" replace />} />
          <Route path="/contracts/*" element={<LegacyContractRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
      <Toaster />
    </>
  );
}

import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { GuestOnly, RequireAuth, RequireRole } from "@/components/common/guards";
import { FullPageLoader } from "@/components/common/loader";
import { AppLayout } from "@/components/layout/AppLayout";

const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/auth/Login"));
const Register = lazy(() => import("@/pages/auth/Register"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Analytics = lazy(() => import("@/pages/Analytics"));
const ModelPerformance = lazy(() => import("@/pages/ModelPerformance"));
const Connect = lazy(() => import("@/pages/Connect"));
const CoverageMap = lazy(() => import("@/pages/CoverageMap"));
const Devices = lazy(() => import("@/pages/Devices"));
const MyComplaints = lazy(() => import("@/pages/MyComplaints"));
const ComplaintDetail = lazy(() => import("@/pages/ComplaintDetail"));
const OperatorDesk = lazy(() => import("@/pages/desk/OperatorDesk"));
const AdminSettings = lazy(() => import("@/pages/admin/Settings"));
const Profile = lazy(() => import("@/pages/Profile"));
const AdminUsers = lazy(() => import("@/pages/admin/Users"));
const NotFound = lazy(() => import("@/pages/NotFound"));
const ProbeApp = lazy(() => import("@/pages/probe/ProbeApp"));

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
        <Route path="/register" element={<GuestOnly><Register /></GuestOnly>} />
        <Route path="/probe" element={<RequireAuth><ProbeApp /></RequireAuth>} />
        <Route path="/app" element={<RequireAuth><AppLayout /></RequireAuth>}>
          <Route index element={<Dashboard />} />
          <Route path="map" element={<CoverageMap />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="models" element={<ModelPerformance />} />
          <Route path="connect" element={<Connect />} />
          <Route path="devices" element={<Devices />} />
          <Route path="complaints" element={<MyComplaints />} />
          <Route path="complaints/:id" element={<ComplaintDetail />} />
          <Route path="desk" element={<RequireRole min="engineer"><OperatorDesk /></RequireRole>} />
          <Route path="settings" element={<RequireRole min="admin"><AdminSettings /></RequireRole>} />
          <Route path="profile" element={<Profile />} />
          <Route path="admin/users" element={<RequireRole min="admin"><AdminUsers /></RequireRole>} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

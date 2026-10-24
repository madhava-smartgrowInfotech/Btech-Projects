import { lazy, Suspense, type ReactNode } from "react";
import { Route, Routes } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";
import { RequireAuth } from "@/lib/auth";

// Every screen is its own chunk, so charts and GSAP only load where they are used.
const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const Register = lazy(() => import("@/pages/Register"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Detect = lazy(() => import("@/pages/Detect"));
const Result = lazy(() => import("@/pages/Result"));
const History = lazy(() => import("@/pages/History"));
const Analytics = lazy(() => import("@/pages/Analytics"));
const Encyclopedia = lazy(() => import("@/pages/Encyclopedia"));
const DiseaseDetail = lazy(() => import("@/pages/DiseaseDetail"));
const Profile = lazy(() => import("@/pages/Profile"));
const NotFound = lazy(() => import("@/pages/NotFound"));

const guard = (node: ReactNode) => <RequireAuth>{node}</RequireAuth>;

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={guard(<Dashboard />)} />
          <Route path="/detect" element={guard(<Detect />)} />
          <Route path="/result/:id" element={guard(<Result />)} />
          <Route path="/history" element={guard(<History />)} />
          <Route path="/analytics" element={guard(<Analytics />)} />
          <Route path="/profile" element={guard(<Profile />)} />
          <Route path="/encyclopedia" element={<Encyclopedia />} />
          <Route path="/disease/:cls" element={<DiseaseDetail />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

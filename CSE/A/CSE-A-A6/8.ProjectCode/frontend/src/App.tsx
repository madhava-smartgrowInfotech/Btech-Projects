import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";
import { RequireAuth } from "@/lib/auth";

// Every screen is its own chunk, so the landing page doesn't pay for recharts, the camera code, etc.
const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const Monitor = lazy(() => import("@/pages/Monitor"));
const History = lazy(() => import("@/pages/History"));
const Thresholds = lazy(() => import("@/pages/Thresholds"));
const Research = lazy(() => import("@/pages/Research"));
const About = lazy(() => import("@/pages/About"));
const NotFound = lazy(() => import("@/pages/NotFound"));

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/app"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<Monitor />} />
          <Route path="history" element={<History />} />
          <Route path="thresholds" element={<Thresholds />} />
          <Route path="research" element={<Research />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

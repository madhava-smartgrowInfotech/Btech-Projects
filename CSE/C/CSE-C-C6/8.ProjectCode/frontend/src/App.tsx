import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";

// Every screen is its own chunk, so charts and GSAP only load where they are used.
const Landing = lazy(() => import("@/pages/Landing"));
const Detect = lazy(() => import("@/pages/Detect"));
const Batch = lazy(() => import("@/pages/Batch"));
const Analytics = lazy(() => import("@/pages/Analytics"));
const Retrain = lazy(() => import("@/pages/Retrain"));
const About = lazy(() => import("@/pages/About"));
const NotFound = lazy(() => import("@/pages/NotFound"));

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Detect />} />
          <Route path="batch" element={<Batch />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="retrain" element={<Retrain />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  );
}

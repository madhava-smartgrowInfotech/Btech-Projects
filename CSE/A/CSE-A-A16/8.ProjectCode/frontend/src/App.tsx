import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { FullPageLoader } from "@/components/ui/Feedback";

// Every screen is its own chunk, so the landing page doesn't pay for recharts, the camera code, etc.
const Landing = lazy(() => import("@/pages/Landing"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Recognize = lazy(() => import("@/pages/Recognize"));
const Collect = lazy(() => import("@/pages/Collect"));
const Train = lazy(() => import("@/pages/Train"));
const Model = lazy(() => import("@/pages/Model"));
const About = lazy(() => import("@/pages/About"));
const NotFound = lazy(() => import("@/pages/NotFound"));

export default function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="recognize" element={<Recognize />} />
          <Route path="collect" element={<Collect />} />
          <Route path="train" element={<Train />} />
          <Route path="model" element={<Model />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

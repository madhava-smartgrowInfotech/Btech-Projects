import { Component, lazy, Suspense, type ComponentType, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";

import { AppShell } from "@/components/ui/AppShell";
import { Button } from "@/components/ui/Button";
import { CardsSkeleton, ErrorState, FullPageLoader, Skeleton } from "@/components/ui/Feedback";
import { useAuth } from "@/lib/auth";

// Every screen is its own chunk: charts, markdown and the landing animations load only where they are used.
const Landing = lazy(() => import("@/pages/Landing"));
const Login = lazy(() => import("@/pages/Login"));
const Overview = lazy(() => import("@/pages/Overview"));
const ReviewNew = lazy(() => import("@/pages/ReviewNew"));
const ReviewResult = lazy(() => import("@/pages/ReviewResult"));
const Codebase = lazy(() => import("@/pages/Codebase"));
const Lab = lazy(() => import("@/pages/Lab"));
const HistoryPage = lazy(() => import("@/pages/History"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));
const About = lazy(() => import("@/pages/About"));
const NotFound = lazy(() => import("@/pages/NotFound"));

function PageFallback() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading page">
      <Skeleton className="h-9 w-64" />
      <CardsSkeleton count={3} />
    </div>
  );
}

function page(Comp: ComponentType) {
  return (
    <Suspense fallback={<PageFallback />}>
      <Comp />
    </Suspense>
  );
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullPageLoader />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return children;
}

/** Last line of defence: a render error shows what failed and a way back instead of a blank page. */
class Boundary extends Component<{ children: ReactNode }, { error: unknown }> {
  state = { error: null as unknown };
  static getDerivedStateFromError(error: unknown) {
    return { error };
  }
  render() {
    if (this.state.error == null) return this.props.children;
    return (
      <div className="mx-auto grid min-h-dvh max-w-lg place-items-center px-4">
        <div className="space-y-4">
          <ErrorState error={this.state.error} title="This screen crashed" hint="Reload the page. If it keeps happening, check the browser console." />
          <Button className="w-full" onClick={() => window.location.assign("/app")}>
            Back to overview
          </Button>
        </div>
      </div>
    );
  }
}

export function App() {
  return (
    <Boundary>
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
            <Route index element={page(Overview)} />
            <Route path="review" element={page(ReviewNew)} />
            <Route path="review/:id" element={page(ReviewResult)} />
            <Route path="codebase" element={page(Codebase)} />
            <Route path="lab" element={page(Lab)} />
            <Route path="history" element={page(HistoryPage)} />
            <Route path="settings" element={page(SettingsPage)} />
            <Route path="about" element={page(About)} />
            <Route path="*" element={page(NotFound)} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </Boundary>
  );
}

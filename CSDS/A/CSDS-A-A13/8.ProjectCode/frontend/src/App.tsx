import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { RequireAuth } from "@/components/common/RequireAuth";
import { FullPageLoader } from "@/components/common/States";
import { AppLayout } from "@/components/layout/AppLayout";

const LandingPage = lazy(() => import("@/pages/public/LandingPage"));
const LoginPage = lazy(() => import("@/pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("@/pages/auth/RegisterPage"));
const DashboardPage = lazy(() => import("@/pages/app/DashboardPage"));
const TeamPage = lazy(() => import("@/pages/app/TeamPage"));
const ImportPage = lazy(() => import("@/pages/app/ImportPage"));
const DataPage = lazy(() => import("@/pages/app/DataPage"));
const SettingsPage = lazy(() => import("@/pages/app/SettingsPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

const page = (element: React.ReactNode) => <Suspense fallback={<FullPageLoader />}>{element}</Suspense>;
const admin = (element: React.ReactNode) => <RequireAuth roles={["admin"]}>{page(element)}</RequireAuth>;

const router = createBrowserRouter([
  { path: "/", element: page(<LandingPage />) },
  { path: "/login", element: page(<LoginPage />) },
  { path: "/register", element: page(<RegisterPage />) },
  {
    path: "/app",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: page(<DashboardPage />) },
      { path: "import", element: admin(<ImportPage />) },
      { path: "data", element: admin(<DataPage />) },
      { path: "team", element: admin(<TeamPage />) },
      { path: "settings", element: admin(<SettingsPage />) },
    ],
  },
  { path: "*", element: page(<NotFoundPage />) },
]);

export default function App() {
  return <RouterProvider router={router} />;
}

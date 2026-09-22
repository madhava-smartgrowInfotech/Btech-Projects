import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import AppLayout from "@/components/layout/AppLayout";
import { RedirectIfAuthed, RequireAdmin, RequireAuth } from "@/components/layout/Guards";
import { FullScreenLoader } from "@/components/common/States";
import { RouteError } from "@/pages/NotFound";

const Landing = lazy(() => import("@/pages/landing/Landing"));
const Login = lazy(() => import("@/pages/auth/Login"));
const Register = lazy(() => import("@/pages/auth/Register"));
const Home = lazy(() => import("@/pages/Home"));
const NotFound = lazy(() => import("@/pages/NotFound"));

const page = (el: ReactNode) => <Suspense fallback={<FullScreenLoader />}>{el}</Suspense>;

const router = createBrowserRouter([
  { path: "/", element: page(<Landing />), errorElement: <RouteError /> },
  { path: "/login", element: page(<RedirectIfAuthed><Login /></RedirectIfAuthed>) },
  { path: "/register", element: page(<RedirectIfAuthed><Register /></RedirectIfAuthed>) },
  {
    path: "/app",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    errorElement: <RouteError />,
    children: [
      { index: true, element: page(<Home />) },
      { path: "*", element: page(<NotFound />) },
    ],
  },
  {
    path: "/admin",
    element: (
      <RequireAuth>
        <RequireAdmin>
          <AppLayout />
        </RequireAdmin>
      </RequireAuth>
    ),
    errorElement: <RouteError />,
    children: [{ index: true, element: <Navigate to="/app" replace /> }],
  },
  { path: "*", element: page(<NotFound />) },
]);

export default function App() {
  return <RouterProvider router={router} />;
}

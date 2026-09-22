import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import AppLayout from "@/components/layout/AppLayout";
import { RedirectIfAuthed, RequireAdmin, RequireAuth } from "@/components/layout/Guards";
import { CardSkeleton, FullScreenLoader } from "@/components/common/States";
import { RouteError } from "@/pages/NotFound";

const Landing = lazy(() => import("@/pages/landing/Landing"));
const Login = lazy(() => import("@/pages/auth/Login"));
const Register = lazy(() => import("@/pages/auth/Register"));
const Home = lazy(() => import("@/pages/Home"));
const Send = lazy(() => import("@/pages/Send"));
const Scan = lazy(() => import("@/pages/Scan"));
const Collect = lazy(() => import("@/pages/Collect"));
const PaymentFlow = lazy(() => import("@/pages/pay/PaymentFlow"));
const SmsCheck = lazy(() => import("@/pages/SmsCheck"));
const History = lazy(() => import("@/pages/History"));
const HistoryDetail = lazy(() => import("@/pages/HistoryDetail"));
const TrustedContacts = lazy(() => import("@/pages/TrustedContacts"));
const Approvals = lazy(() => import("@/pages/Approvals"));
const Settings = lazy(() => import("@/pages/Settings"));
const ModelPerformance = lazy(() => import("@/pages/ModelPerformance"));
const Sandbox = lazy(() => import("@/pages/Sandbox"));
const Analytics = lazy(() => import("@/pages/admin/Analytics"));
const NotFound = lazy(() => import("@/pages/NotFound"));

const full = (el: ReactNode) => <Suspense fallback={<FullScreenLoader />}>{el}</Suspense>;
const inner = (el: ReactNode) => <Suspense fallback={<CardSkeleton rows={5} />}>{el}</Suspense>;

const router = createBrowserRouter([
  { path: "/", element: full(<Landing />), errorElement: <RouteError /> },
  { path: "/login", element: full(<RedirectIfAuthed><Login /></RedirectIfAuthed>) },
  { path: "/register", element: full(<RedirectIfAuthed><Register /></RedirectIfAuthed>) },
  {
    path: "/app",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    errorElement: <RouteError />,
    children: [
      { index: true, element: inner(<Home />) },
      { path: "send", element: inner(<Send />) },
      { path: "scan", element: inner(<Scan />) },
      { path: "collect", element: inner(<Collect />) },
      { path: "pay/:id", element: inner(<PaymentFlow />) },
      { path: "sms", element: inner(<SmsCheck />) },
      { path: "history", element: inner(<History />) },
      { path: "history/:id", element: inner(<HistoryDetail />) },
      { path: "trusted", element: inner(<TrustedContacts />) },
      { path: "approvals", element: inner(<Approvals />) },
      { path: "settings", element: inner(<Settings />) },
      { path: "models", element: inner(<ModelPerformance />) },
      { path: "sandbox", element: inner(<Sandbox />) },
      { path: "*", element: inner(<NotFound />) },
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
    children: [{ index: true, element: inner(<Analytics />) }],
  },
  { path: "*", element: full(<NotFound />) },
]);

export default function App() {
  return <RouterProvider router={router} />;
}

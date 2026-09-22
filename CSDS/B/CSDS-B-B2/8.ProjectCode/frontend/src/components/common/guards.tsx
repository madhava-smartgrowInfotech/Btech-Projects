import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { hasRole, type Role } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { EmptyState } from "./states";
import { FullPageLoader } from "./loader";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, token, loading } = useAuth();
  const location = useLocation();
  if (token && loading) return <FullPageLoader />;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  return <>{children}</>;
}

export function RequireRole({ min, children }: { min: Role; children: ReactNode }) {
  const { user } = useAuth();
  if (!hasRole(user, min)) {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="You don't have access to this page"
        description={`This area is for ${min === "admin" ? "administrators" : "network engineers and administrators"}. Ask an administrator to change your role.`}
      />
    );
  }
  return <>{children}</>;
}

export function GuestOnly({ children }: { children: ReactNode }) {
  const { user, token, loading } = useAuth();
  if (token && loading) return <FullPageLoader />;
  if (user) return <Navigate to="/app" replace />;
  return <>{children}</>;
}

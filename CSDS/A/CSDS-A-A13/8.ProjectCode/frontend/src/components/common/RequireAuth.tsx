import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { ErrorState, FullPageLoader } from "@/components/common/States";
import { useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

export function RequireAuth({ children, roles }: { children: ReactNode; roles?: Role[] }) {
  const { user, token, loading, error, retry } = useAuth();
  const location = useLocation();

  if (!token) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  if (error && !user) {
    return (
      <div className="flex min-h-dvh items-center justify-center p-4">
        <ErrorState error={error} onRetry={retry} title="SeatWise could not load your account" className="w-full max-w-md" />
      </div>
    );
  }
  if (loading || !user) return <FullPageLoader />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/app" replace />;
  return <>{children}</>;
}

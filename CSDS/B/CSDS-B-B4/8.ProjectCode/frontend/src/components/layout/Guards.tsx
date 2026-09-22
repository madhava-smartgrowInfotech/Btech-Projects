import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { FullScreenLoader } from "@/components/common/States";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { token, user, isLoading } = useAuth();
  const location = useLocation();
  if (!token) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (isLoading || !user) return <FullScreenLoader />;
  return <>{children}</>;
}

export function RequireAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user && user.role !== "admin") return <Navigate to="/app" replace />;
  return <>{children}</>;
}

export function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { token, user } = useAuth();
  if (token && user) return <Navigate to={user.role === "admin" ? "/admin" : "/app"} replace />;
  return <>{children}</>;
}

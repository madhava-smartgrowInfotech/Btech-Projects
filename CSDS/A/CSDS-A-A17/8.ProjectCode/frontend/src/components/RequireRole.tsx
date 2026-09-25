import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/lib/authStore";
import type { Role } from "@/types";

const ROLE_HOME: Record<Role, string> = {
  farmer: "/farmer",
  buyer: "/buyer",
  distributor: "/distributor",
  admin: "/admin",
};

export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role]} replace />;
  return <>{children}</>;
}

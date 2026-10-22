import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router";

import { FullPageLoader } from "@/components/ui/Feedback";
import { api, getToken, setToken, type User } from "@/lib/api";

interface AuthValue {
  user: User | null;
  loading: boolean;
  signIn: (identifier: string, password: string) => Promise<void>;
  signOut: () => void;
  setUser: (user: User) => void;
  /** True right after the user chose to log out, so guards send them home instead of to the login form. */
  leftOnPurpose: React.MutableRefObject<boolean>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(() => !!getToken());
  const leftOnPurpose = useRef(false);

  useEffect(() => {
    if (!getToken()) return;
    api
      .get<User>("/auth/me")
      .then((r) => setUserState(r.data))
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const signOut = useCallback(() => {
    setToken(null);
    setUserState(null);
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => {
    const onExpired = () => signOut();
    window.addEventListener("finjarvis:signed-out", onExpired);
    return () => window.removeEventListener("finjarvis:signed-out", onExpired);
  }, [signOut]);

  const signIn = useCallback(
    async (identifier: string, password: string) => {
      const r = await api.post<{ token: string; user: User }>("/auth/login", { identifier, password });
      leftOnPurpose.current = false;
      queryClient.clear();
      setToken(r.data.token);
      setUserState(r.data.user);
    },
    [queryClient],
  );

  const value = useMemo<AuthValue>(
    () => ({ user, loading, signIn, signOut, setUser: setUserState, leftOnPurpose }),
    [user, loading, signIn, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

/** Route guard for the signed-in app. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading, leftOnPurpose } = useAuth();
  const location = useLocation();
  if (loading) return <FullPageLoader />;
  if (!user) {
    if (leftOnPurpose.current) return <Navigate to="/" replace />;
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}

/** Keeps signed-in users away from the login and signup forms. */
export function GuestOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <FullPageLoader />;
  if (user) return <Navigate to="/app" replace />;
  return <>{children}</>;
}

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import api from "@/lib/api";
import type { AuthResponse, UserSummary } from "@/lib/types";

interface AuthContextValue {
  user: UserSummary | null;
  login: (email: string, password: string) => Promise<UserSummary>;
  register: (name: string, email: string, password: string) => Promise<UserSummary>;
  logout: () => void;
  markProfile: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredUser(): UserSummary | null {
  try {
    const raw = localStorage.getItem("ns_user");
    return raw ? (JSON.parse(raw) as UserSummary) : null;
  } catch {
    return null;
  }
}

/** Session = a bearer token plus a cached user summary. The API stays the source of truth on every call. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSummary | null>(readStoredUser);

  const save = useCallback((data: AuthResponse) => {
    localStorage.setItem("ns_token", data.token);
    localStorage.setItem("ns_user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  const login = useCallback(
    async (email: string, password: string) => save((await api.post<AuthResponse>("/auth/login", { email, password })).data),
    [save],
  );

  const register = useCallback(
    async (name: string, email: string, password: string) =>
      save((await api.post<AuthResponse>("/auth/register", { name, email, password })).data),
    [save],
  );

  const markProfile = useCallback(() => {
    setUser((prev) => {
      if (!prev) return prev;
      const next = { ...prev, has_profile: true };
      localStorage.setItem("ns_user", JSON.stringify(next));
      return next;
    });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("ns_token");
    localStorage.removeItem("ns_user");
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, login, register, logout, markProfile }), [user, login, register, logout, markProfile]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

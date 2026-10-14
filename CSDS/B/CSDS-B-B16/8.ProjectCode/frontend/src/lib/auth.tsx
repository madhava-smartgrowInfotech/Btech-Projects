import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { api, clearSession, getToken, loadUser, saveSession } from "@/lib/api";
import type { AuthUser, LoginResponse } from "@/lib/types";

interface AuthValue {
  user: AuthUser | null;
  signedIn: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

/** Holds the signed-in user. The token itself lives in localStorage and is attached by the API client. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(() => (getToken() ? loadUser() : null));

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post<LoginResponse>("/auth/login", { email, password });
    saveSession(data.token, data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  const value = useMemo(() => ({ user, signedIn: user !== null, login, logout }), [user, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

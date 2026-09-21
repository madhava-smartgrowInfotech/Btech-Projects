import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, getToken, setToken, setUnauthorizedHandler } from "@/lib/api";
import type { TokenResponse, User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (fullName: string, email: string, password: string) => Promise<User>;
  logout: () => void;
  updateUser: (patch: Partial<Pick<User, "full_name" | "language" | "theme">>) => Promise<User>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(() => Boolean(getToken()));
  const queryClient = useQueryClient();

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
      queryClient.clear();
    });
    return () => setUnauthorizedHandler(null);
  }, [queryClient]);

  useEffect(() => {
    if (!getToken()) return;
    let cancelled = false;
    api
      .get<User>("/auth/me")
      .then((res) => !cancelled && setUser(res.data))
      .catch(() => !cancelled && setToken(null))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const accept = useCallback((data: TokenResponse) => {
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const login = useCallback(
    async (email: string, password: string) => accept((await api.post<TokenResponse>("/auth/login", { email, password })).data),
    [accept],
  );

  const register = useCallback(
    async (fullName: string, email: string, password: string) =>
      accept((await api.post<TokenResponse>("/auth/register", { full_name: fullName, email, password })).data),
    [accept],
  );

  const updateUser = useCallback(async (patch: Partial<Pick<User, "full_name" | "language" | "theme">>) => {
    const res = await api.patch<User>("/users/me", patch);
    setUser(res.data);
    return res.data;
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, updateUser }),
    [user, loading, login, register, logout, updateUser],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

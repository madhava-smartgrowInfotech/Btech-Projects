import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, setUnauthorizedHandler, TOKEN_KEY, type TokenResponse, type User } from "./api";
import { safeStorage } from "./utils";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string) => Promise<User>;
  logout: () => void;
  setUser: (u: User) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [token, setToken] = useState<string | null>(() => safeStorage.get(TOKEN_KEY));

  const me = useQuery({
    queryKey: ["me", token],
    enabled: !!token,
    queryFn: async () => (await api.get<User>("/api/auth/me")).data,
    staleTime: 60_000,
    retry: (count, err: unknown) => count < 2 && (err as { response?: { status?: number } })?.response?.status !== 401,
  });

  const logout = useCallback(() => {
    safeStorage.remove(TOKEN_KEY);
    setToken(null);
    qc.clear();
  }, [qc]);

  useEffect(() => {
    setUnauthorizedHandler(() => logout());
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  const accept = useCallback(
    (res: TokenResponse) => {
      safeStorage.set(TOKEN_KEY, res.access_token);
      qc.setQueryData(["me", res.access_token], res.user);
      setToken(res.access_token);
      return res.user;
    },
    [qc],
  );

  const value = useMemo<AuthState>(
    () => ({
      user: token ? (me.data ?? null) : null,
      token,
      loading: !!token && me.isPending,
      login: async (email, password) => accept((await api.post<TokenResponse>("/api/auth/login", { email, password })).data),
      register: async (name, email, password) =>
        accept((await api.post<TokenResponse>("/api/auth/register", { name, email, password })).data),
      logout,
      setUser: (u) => qc.setQueryData(["me", token], u),
    }),
    [token, me.data, me.isPending, accept, logout, qc],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

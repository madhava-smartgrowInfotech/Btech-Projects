import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, TOKEN_KEY, UNAUTHORIZED_EVENT } from "@/lib/api";
import { storage } from "@/lib/storage";
import type { TokenResponse, User } from "@/lib/types";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: unknown;
  retry: () => void;
  login: (email: string, password: string) => Promise<User>;
  logout: (message?: string) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => storage.get(TOKEN_KEY));

  const me = useQuery({
    queryKey: ["me", token],
    queryFn: async () => (await api.get<User>("/auth/me")).data,
    enabled: Boolean(token),
    staleTime: 5 * 60_000,
    retry: false,
  });

  const logout = useCallback(
    (message?: string) => {
      storage.remove(TOKEN_KEY);
      setToken(null);
      queryClient.clear();
      if (message) toast.info(message);
    },
    [queryClient],
  );

  useEffect(() => {
    const onUnauthorized = () => logout("Your session has ended. Please sign in again.");
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, [logout]);

  const login = useCallback(
    async (email: string, password: string) => {
      const { data } = await api.post<TokenResponse>("/auth/login", { email, password });
      storage.set(TOKEN_KEY, data.access_token);
      queryClient.setQueryData(["me", data.access_token], data.user);
      setToken(data.access_token);
      return data.user;
    },
    [queryClient],
  );

  const value = useMemo<AuthState>(
    () => ({
      user: token ? (me.data ?? null) : null,
      token,
      loading: Boolean(token) && me.isPending,
      error: me.error,
      retry: () => void me.refetch(),
      login,
      logout,
    }),
    [token, me, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

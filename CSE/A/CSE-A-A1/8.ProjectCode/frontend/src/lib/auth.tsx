import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";

import { api, type User } from "@/lib/api";
import { keys } from "@/lib/queries";

interface AuthValue {
  user: User | null;
  /** True only while the very first "who am I" check is in flight. */
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, interests: string) => Promise<void>;
  logout: () => Promise<void>;
}

/** Forget every cached screen except the "who am I" query, so the next user never sees the last user's data. */
function dropUserData(qc: QueryClient) {
  qc.removeQueries({ predicate: (q) => q.queryKey[0] !== keys.me[0] });
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const me = useQuery({
    queryKey: keys.me,
    queryFn: async () => (await api.get<User | null>("/auth/me")).data,
    retry: false,
    staleTime: 5 * 60_000,
  });

  const login = useCallback(
    async (username: string, password: string) => {
      const { data } = await api.post<User>("/auth/login", { username, password });
      dropUserData(qc);
      qc.setQueryData(keys.me, data);
    },
    [qc],
  );

  const register = useCallback(async (username: string, password: string, interests: string) => {
    await api.post("/auth/register", { username, password, interests });
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      dropUserData(qc);
      qc.setQueryData(keys.me, null);
    }
  }, [qc]);

  const value = useMemo<AuthValue>(
    () => ({ user: me.data ?? null, loading: me.isPending, login, register, logout }),
    [me.data, me.isPending, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

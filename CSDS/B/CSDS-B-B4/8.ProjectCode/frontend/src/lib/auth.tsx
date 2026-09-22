import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, TOKEN_KEY } from "@/lib/api";
import { storage } from "@/lib/storage";
import { useI18n, type Language } from "@/lib/i18n";

export interface Me {
  id: number;
  full_name: string;
  phone: string;
  email: string | null;
  role: "user" | "admin";
  is_sample: boolean;
  upi_id: string;
  balance: number;
  language: Language;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  user: Me;
}

export interface RegisterInput {
  full_name: string;
  phone: string;
  email?: string;
  password: string;
  pin: string;
  language: Language;
}

interface AuthState {
  token: string | null;
  user: Me | undefined;
  isLoading: boolean;
  login: (identifier: string, password: string) => Promise<Me>;
  register: (input: RegisterInput) => Promise<Me>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const { setLang } = useI18n();
  const [token, setToken] = useState<string | null>(() => storage.get(TOKEN_KEY));

  const me = useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<Me>("/auth/me")).data,
    enabled: !!token,
    staleTime: 15_000,
  });

  const accept = useCallback(
    (res: TokenResponse) => {
      storage.set(TOKEN_KEY, res.access_token);
      setToken(res.access_token);
      qc.setQueryData(["me"], res.user);
      setLang(res.user.language);
      return res.user;
    },
    [qc, setLang],
  );

  const login = useCallback(
    async (identifier: string, password: string) => accept((await api.post<TokenResponse>("/auth/login", { identifier, password })).data),
    [accept],
  );

  const register = useCallback(
    async (input: RegisterInput) => accept((await api.post<TokenResponse>("/auth/register", input)).data),
    [accept],
  );

  const logout = useCallback(() => {
    storage.remove(TOKEN_KEY);
    setToken(null);
    qc.clear();
  }, [qc]);

  useEffect(() => {
    const onLogout = () => {
      setToken(null);
      qc.clear();
    };
    window.addEventListener("upg:logout", onLogout);
    return () => window.removeEventListener("upg:logout", onLogout);
  }, [qc]);

  const value = useMemo<AuthState>(
    () => ({ token, user: me.data, isLoading: !!token && me.isLoading, login, register, logout }),
    [token, me.data, me.isLoading, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

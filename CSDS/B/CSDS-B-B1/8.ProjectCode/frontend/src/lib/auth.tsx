import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { api, TOKEN_KEY, USER_KEY } from "@/lib/api";
import type { Role, User } from "@/lib/types";

interface AuthValue {
  user: User | null;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

function stored(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw && localStorage.getItem(TOKEN_KEY) ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(stored);

  const save = useCallback(({ token, user }: { token: string; user: User }) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    setUser(user);
    return user;
  }, []);

  const value = useMemo<AuthValue>(
    () => ({
      user,
      login: async (email, password) => save((await api.post("/auth/login", { email, password })).data),
      register: async (name, email, password) => save((await api.post("/auth/register", { name, email, password })).data),
      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        setUser(null);
      },
    }),
    [user, save],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

export const isStaff = (role: Role | undefined) => role === "officer" || role === "admin";

export function homeFor(user: User | null) {
  if (!user) return "/login";
  return user.role === "citizen" ? "/app/track" : "/app/queue";
}

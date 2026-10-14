import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { queryClient } from "@/lib/queries";

export type Role = "patient" | "doctor" | "staff" | "admin";

export interface SessionUser {
  username: string;
  role: Role;
  display_name: string;
  hospital: string | null;
  hospital_name: string | null;
}

interface AuthValue {
  user: SessionUser | null;
  login: (token: string, user: SessionUser) => void;
  logout: () => void;
}

/** Where each role lands after sign-in. */
export const HOME: Record<Role, string> = {
  patient: "/patient",
  doctor: "/doctor",
  staff: "/hospital",
  admin: "/hospital",
};

const AuthContext = createContext<AuthValue | null>(null);

function readUser(): SessionUser | null {
  try {
    const raw = window.localStorage.getItem("uh_user");
    return raw ? (JSON.parse(raw) as SessionUser) : null;
  } catch {
    return null;
  }
}

function writeStorage(token: string | null, user: SessionUser | null) {
  try {
    if (token && user) {
      window.localStorage.setItem("uh_token", token);
      window.localStorage.setItem("uh_user", JSON.stringify(user));
    } else {
      window.localStorage.removeItem("uh_token");
      window.localStorage.removeItem("uh_user");
    }
  } catch {
    /* storage blocked: the session lasts until the tab reloads */
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(readUser);

  const login = useCallback((token: string, next: SessionUser) => {
    writeStorage(token, next);
    queryClient.clear();
    setUser(next);
  }, []);

  const logout = useCallback(() => {
    writeStorage(null, null);
    queryClient.clear();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

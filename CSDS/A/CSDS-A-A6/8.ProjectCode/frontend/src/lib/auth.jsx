import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { SESSION_EXPIRED_EVENT } from "./api.js";

const AuthContext = createContext(null);

// Shape the kit's app shell expects: a user with a display name, plus logout and updateUser.
function userFromEmail(email) {
  const local = email.split("@")[0] || "";
  const full_name = local.replace(/[._-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) || email;
  return { email, full_name };
}

export function AuthProvider({ children }) {
  const [email, setEmail] = useState(() => localStorage.getItem("clauseguard_email") || "");
  const [token, setToken] = useState(() => localStorage.getItem("clauseguard_token") || "");

  const login = useCallback((newToken, newEmail) => {
    localStorage.setItem("clauseguard_token", newToken);
    localStorage.setItem("clauseguard_email", newEmail);
    setToken(newToken);
    setEmail(newEmail);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("clauseguard_token");
    localStorage.removeItem("clauseguard_email");
    setToken("");
    setEmail("");
  }, []);

  // There is no server-side user settings endpoint, so the theme persists locally (ThemeProvider).
  const updateUser = useCallback(() => Promise.resolve(), []);

  useEffect(() => {
    function onExpired() {
      if (!localStorage.getItem("clauseguard_token")) return;
      logout();
      toast.error("Your session expired. Please log in again.");
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, [logout]);

  const user = useMemo(() => (token && email ? userFromEmail(email) : null), [token, email]);

  const value = useMemo(
    () => ({ email, token, user, isAuthenticated: !!token, login, logout, updateUser }),
    [email, token, user, login, logout, updateUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

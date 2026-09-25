import { createContext, useContext, useState, useCallback } from "react";

const AuthContext = createContext(null);

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

  return (
    <AuthContext.Provider value={{ email, token, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

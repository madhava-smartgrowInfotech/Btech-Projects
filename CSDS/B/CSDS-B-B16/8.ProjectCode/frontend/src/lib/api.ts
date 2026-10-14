import axios, { isAxiosError } from "axios";

import type { AuthUser } from "@/lib/types";

// Same keys as the previous build, so a signed-in browser stays signed in after the rebuild.
export const TOKEN_KEY = "rg_token";
export const USER_KEY = "rg_user";

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  return readStorage(TOKEN_KEY);
}

export function loadUser(): AuthUser | null {
  const raw = readStorage(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function saveSession(token: string, user: AuthUser) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    /* storage blocked: the session lasts for this tab only */
  }
}

export function clearSession() {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    /* nothing stored */
  }
}

export const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = String(error?.config?.url ?? "");
    if (error?.response?.status === 401 && !url.includes("/auth/login")) {
      clearSession();
      if (!window.location.pathname.startsWith("/login")) window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

interface ApiErrorBody {
  detail?: string | { loc?: (string | number)[]; msg?: string }[];
}

/** Says what failed, using the API's own message when it has one. */
export function errorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const data = error.response?.data as ApiErrorBody | Blob | undefined;
    if (data instanceof Blob) return "The request failed. Try again in a moment.";
    const detail = data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => `${String(item.loc?.slice(-1)[0] ?? "field")}: ${item.msg ?? "invalid"}`).join("; ");
    }
    if (error.message === "Network Error") return "Cannot reach the RetinaGuard server. Is the backend running?";
    return error.message || "Something went wrong";
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}

export const pct = (p: number | null | undefined) => (p == null ? "-" : `${Math.round(p * 100)}%`);

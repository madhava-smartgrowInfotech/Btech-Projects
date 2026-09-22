import axios, { AxiosError } from "axios";
import { safeStorage } from "./utils";

export const TOKEN_KEY = "signalscout-token";

/** Same-origin API: the dev server proxies /api to the backend; production is served by the backend itself. */
export const api = axios.create({ baseURL: "/", timeout: 20000 });

api.interceptors.request.use((config) => {
  const token = safeStorage.get(TOKEN_KEY);
  if (token) config.headers.set("Authorization", `Bearer ${token}`);
  return config;
});

type Unauthorized = () => void;
let onUnauthorized: Unauthorized | null = null;
export function setUnauthorizedHandler(fn: Unauthorized | null) {
  onUnauthorized = fn;
}

api.interceptors.response.use(
  (r) => r,
  (error: AxiosError) => {
    const url = error.config?.url ?? "";
    if (error.response?.status === 401 && !url.includes("/api/auth/login") && onUnauthorized) onUnauthorized();
    return Promise.reject(error);
  },
);

/** A readable message for any API error (FastAPI detail string, validation list, network failure). */
export function apiError(err: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(err)) {
    if (!err.response) {
      return navigator.onLine ? "Cannot reach the SignalScout server. Is it running?" : "You are offline. Changes will sync when you reconnect.";
    }
    const detail = (err.response.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0] as { loc?: unknown[]; msg?: string };
      const field = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : "";
      const msg = (first.msg ?? "is invalid").replace(/^Value error, /, "");
      return field && field !== "body" ? `${field.replace(/_/g, " ")}: ${msg}` : msg;
    }
    return `${fallback} (HTTP ${err.response.status})`;
  }
  return err instanceof Error ? err.message : fallback;
}

export type Role = "user" | "engineer" | "admin";

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  notify_email: boolean;
  is_demo: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Health {
  status: "ok" | "degraded";
  app: string;
  version: string;
  time: string;
  database: string;
  models: Record<string, boolean>;
}

export interface ConnectInfo {
  tunnel_url: string | null;
  tunnel_started_at: string | null;
  probe_url: string | null;
  tunnel_enabled: boolean;
  lan_api_urls: string[];
  lan_dashboard_urls: string[];
  backend_port: number;
  frontend_port: number;
}

export const ROLE_RANK: Record<Role, number> = { user: 0, engineer: 1, admin: 2 };
export const hasRole = (user: User | null | undefined, min: Role) => !!user && ROLE_RANK[user.role] >= ROLE_RANK[min];

import axios, { AxiosError } from "axios";

// Same-origin: Vite proxies /api to the FastAPI backend, which sets the httpOnly session cookie.
export const api = axios.create({ baseURL: "/api", timeout: 30_000, withCredentials: true });

let csrfToken: string | null = null;
export function setCsrf(token: string | null) {
  csrfToken = token;
}

api.interceptors.request.use((config) => {
  if (csrfToken && config.method && config.method !== "get") config.headers["X-CSRF-Token"] = csrfToken;
  return config;
});

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? "";
    if (error.response?.status === 401 && !url.includes("/auth/login") && !url.includes("/auth/me")) {
      setCsrf(null);
      onUnauthorized?.();
    }
    return Promise.reject(error);
  },
);

interface ApiErrorBody {
  detail?: string | { msg?: string }[];
}

/** A readable message for any API or network error. */
export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNABORTED") return "The request took too long. Please try again.";
    if (!error.response) return "Cannot reach the AegisBallot server. Make sure it is running (run.bat).";
    const data = error.response.data as ApiErrorBody | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    if (error.response.status === 403) return "You do not have permission to do that.";
    if (error.response.status === 404) return "That item was not found.";
    if (error.response.status === 429) return "Too many attempts. Please wait a minute and try again.";
    if (error.response.status >= 500) return "The server hit an error. Please try again.";
  }
  return error instanceof Error && error.message ? error.message : fallback;
}

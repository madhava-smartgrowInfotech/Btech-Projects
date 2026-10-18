import axios, { AxiosError } from "axios";

const TOKEN_KEY = "autosecai-token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the session just lasts until reload */
  }
}

/** Same-origin `/api` (Vite proxies it to the FastAPI backend on BACKEND_PORT). */
export const api = axios.create({ baseURL: "/api", timeout: 120_000 });

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: (() => void) | null) {
  onUnauthorized = fn;
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error: AxiosError) => {
    // an expired or revoked session on a protected call sends the user back to sign in
    if (error.response?.status === 401 && getToken() && !error.config?.url?.startsWith("/auth/login")) onUnauthorized?.();
    return Promise.reject(error);
  },
);

/** The API's own message when there is one, otherwise a plain description of what went wrong. */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => (d as { msg?: string }).msg).filter(Boolean).join("; ") || "The request was not valid.";
    if (!error.response) return "Can't reach the AutoSecAI API. Is the backend running (run.bat)?";
    if (error.code === "ECONNABORTED") return "The request took too long. Try again.";
    return `The server returned ${error.response.status}.`;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

/** Download an authenticated file (export / patched source) through the browser's save dialog. */
export async function download(path: string, fallbackName: string) {
  const res = await api.get(path, { responseType: "blob" });
  const cd = String(res.headers["content-disposition"] ?? "");
  const name = /filename="?([^";]+)"?/.exec(cd)?.[1] ?? fallbackName;
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  return name;
}

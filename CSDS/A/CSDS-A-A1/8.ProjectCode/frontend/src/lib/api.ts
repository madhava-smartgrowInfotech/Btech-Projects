import axios, { AxiosError } from "axios";

const TOKEN_KEY = "policylens-token";

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
    /* ignore - the session then lasts for this tab only */
  }
}

export const api = axios.create({ baseURL: "/api", timeout: 180_000 });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
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
    if (error.response?.status === 401 && !url.includes("/auth/login") && !url.includes("/auth/register")) {
      setToken(null);
      onUnauthorized?.();
    }
    return Promise.reject(error);
  },
);

interface ApiErrorBody {
  detail?: string | { msg?: string }[];
  code?: string;
}

/** A readable message for any API or network error. */
export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNABORTED") return "The request took too long. Please try again.";
    if (!error.response) return "Can't reach the PolicyLens server. Make sure it is running (run.bat).";
    const data = error.response.data as ApiErrorBody | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    if (error.response.status >= 500) return "The server hit a problem. Please try again.";
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function errorCode(error: unknown): string | undefined {
  if (axios.isAxiosError(error)) return (error.response?.data as ApiErrorBody | undefined)?.code;
  return undefined;
}

/** Fetch a protected binary resource (PDF page image, original PDF) as an object URL. */
export async function fetchBlobUrl(url: string): Promise<string> {
  const res = await api.get(url, { responseType: "blob" });
  return URL.createObjectURL(res.data as Blob);
}

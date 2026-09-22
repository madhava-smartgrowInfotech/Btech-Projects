import axios, { AxiosError } from "axios";
import { storage } from "@/lib/storage";

export const TOKEN_KEY = "upg.token";

export const api = axios.create({ baseURL: "/api", timeout: 30000 });

api.interceptors.request.use((config) => {
  const token = storage.get(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401 && storage.get(TOKEN_KEY)) {
      storage.remove(TOKEN_KEY);
      window.dispatchEvent(new Event("upg:logout"));
    }
    return Promise.reject(error);
  },
);

export interface ApiErrorDetail {
  code: string;
  message: string;
  field?: string;
}

/** Returns the API's stable error code and message, or a network message. */
export function apiError(err: unknown): ApiErrorDetail {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (detail && typeof detail === "object" && "code" in detail) return detail as ApiErrorDetail;
    if (typeof detail === "string") return { code: "error", message: detail };
    if (!err.response) return { code: "network", message: "Cannot reach UPI Guardian. Check that it is running and try again." };
    return { code: `http_${err.response.status}`, message: err.message };
  }
  return { code: "error", message: err instanceof Error ? err.message : "Unexpected error" };
}

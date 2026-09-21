import axios, { AxiosError } from "axios";
import { storage } from "@/lib/storage";

export const TOKEN_KEY = "seatwise.token";
export const UNAUTHORIZED_EVENT = "seatwise:unauthorized";

export const api = axios.create({ baseURL: "/api", timeout: 180_000 });

api.interceptors.request.use((config) => {
  const token = storage.get(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? "";
    if (error.response?.status === 401 && !url.includes("/auth/login") && storage.get(TOKEN_KEY)) {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    return Promise.reject(error);
  },
);

interface ErrorBody {
  detail?: string | { msg: string }[];
  details?: unknown;
}

/** A readable message for any API failure. */
export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return error.code === "ECONNABORTED"
        ? "The server took too long to answer. Please try again."
        : "Cannot reach the SeatWise server. Check that run.bat is still running.";
    }
    const body = error.response.data as ErrorBody | undefined;
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) return body.detail.map((d) => d.msg).join("; ");
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function errorDetails<T = unknown>(error: unknown): T | undefined {
  if (axios.isAxiosError(error)) return (error.response?.data as ErrorBody | undefined)?.details as T | undefined;
  return undefined;
}

function filenameFrom(disposition: string | undefined, fallback: string) {
  const match = disposition?.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
  return match ? decodeURIComponent(match[1]) : fallback;
}

/** Download a file from the API (with the sign-in token) and save it. */
export async function downloadFile(url: string, fallbackName: string, params?: Record<string, unknown>) {
  const response = await api.get<Blob>(url, { responseType: "blob", params });
  const name = filenameFrom(response.headers["content-disposition"] as string | undefined, fallbackName);
  const href = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = href;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(href), 10_000);
  return name;
}

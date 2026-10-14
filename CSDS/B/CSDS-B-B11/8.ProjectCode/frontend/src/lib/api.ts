import axios, { isAxiosError } from "axios";

// Same-origin "/api": Vite proxies it to the FastAPI backend (see vite.config.ts).
const api = axios.create({ baseURL: "/api", timeout: 120_000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ns_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err: unknown) => {
    // An expired session sends the user back to log in. Login/register failures stay on their form.
    if (isAxiosError(err) && err.response?.status === 401 && !err.config?.url?.startsWith("/auth/")) {
      localStorage.removeItem("ns_token");
      localStorage.removeItem("ns_user");
      if (window.location.pathname !== "/login") window.location.assign("/login");
    }
    return Promise.reject(err);
  },
);

/** Turns any API failure into one sentence the user can act on. */
export function errorMessage(err: unknown): string {
  if (isAxiosError(err)) {
    const d = err.response?.data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d.map((x: { loc?: unknown[]; msg?: string }) => `${String(x.loc?.slice(-1)[0] ?? "")}: ${x.msg ?? ""}`.replace(/^: /, "")).join("; ");
    }
    if (err.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (!err.response) return "Cannot reach the NutriSense server. Is the backend running?";
    if (err.response.status === 503) return "This service is unavailable right now. Please try again in a moment.";
  }
  return "Something went wrong. Please try again.";
}

/** Local calendar date as YYYY-MM-DD (the API keys days by date, not by UTC). */
export function today(): string {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

export default api;

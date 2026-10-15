import axios, { isAxiosError } from "axios";

export const TOKEN_KEY = "cp_token";
export const USER_KEY = "cp_user";

export const api = axios.create({ baseURL: "/api", timeout: 180_000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (isAxiosError(err) && err.response?.status === 401 && !String(err.config?.url).includes("/auth/login")) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      if (!location.pathname.startsWith("/login")) location.assign("/login");
    }
    return Promise.reject(err);
  },
);

/** The API's own message when it sent one, otherwise a plain-language fallback. */
export function errorMessage(err: unknown): string {
  if (isAxiosError(err)) {
    const d = err.response?.data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x: { msg: string }) => x.msg).join(", ");
    if (err.code === "ERR_NETWORK") return "Cannot reach the CivicPulse server. Is the backend running?";
    return err.message;
  }
  return err instanceof Error ? err.message : "Something went wrong";
}

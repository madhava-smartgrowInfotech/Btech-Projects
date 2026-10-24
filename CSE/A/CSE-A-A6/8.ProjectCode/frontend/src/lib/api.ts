import axios from "axios";

import type {
  About,
  AppConfig,
  AuthUser,
  Health,
  HistoryPayload,
  ResearchPayload,
  SessionState,
  SettingsPayload,
} from "@/lib/types";

export const TOKEN_KEY = "smartrider-token";

export const api = axios.create({ baseURL: "/api", timeout: 30_000 });

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
    /* storage unavailable - the token then lives only in memory for this page */
    memoryToken = token;
  }
}

let memoryToken: string | null = null;

api.interceptors.request.use((config) => {
  const token = getToken() ?? memoryToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/** Fired when the API answers 401 on a signed-in call, so the app can send the user back to the login page. */
export const AUTH_EXPIRED_EVENT = "smartrider:auth-expired";

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401 && !String(error.config?.url).includes("/auth/login")) {
      setToken(null);
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
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
    if (!error.response) return "Can't reach the Smart Rider server. Make sure it is running (run.bat).";
    const data = error.response.data as ApiErrorBody | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    return `${fallback} (${error.response.status})`;
  }
  return error instanceof Error ? error.message : fallback;
}

export function httpStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined;
}

const get = async <T>(url: string) => (await api.get<T>(url)).data;

export const endpoints = {
  health: () => get<Health>("/health"),
  config: () => get<AppConfig>("/config"),
  about: () => get<About>("/about"),
  demo: () => get<{ email: string; password: string }>("/auth/demo"),
  login: async (email: string, password: string) =>
    (await api.post<{ token: string; user: AuthUser }>("/auth/login", { email, password })).data,
  me: () => get<AuthUser>("/auth/me"),

  createSession: async () => (await api.post<SessionState>("/session")).data,
  closeSession: async (id: string) => (await api.delete<{ closed: boolean }>(`/session/${id}`)).data,
  session: (id: string) => get<SessionState>(`/session/${id}`),
  setSource: async (id: string, source: string, scenario?: string) =>
    (await api.post<SessionState>(`/session/${id}/source`, { source, scenario })).data,
  setMonitoring: async (id: string, active: boolean) =>
    (await api.post<SessionState>(`/session/${id}/monitoring`, { active })).data,
  setCalibration: async (id: string, active: boolean) =>
    (await api.post<SessionState>(`/session/${id}/calibration`, { active })).data,
  frame: async (id: string, frame: Blob) => {
    const form = new FormData();
    form.append("frame", frame, "frame.jpg");
    return (await api.post<SessionState>(`/session/${id}/frame`, form, { timeout: 15_000 })).data;
  },
  tick: async (id: string) => (await api.post<SessionState>(`/session/${id}/tick`)).data,

  settings: () => get<SettingsPayload>("/settings"),
  saveSettings: async (body: Record<string, number>) => (await api.put<SettingsPayload>("/settings", body)).data,

  history: (limit = 500) => get<HistoryPayload>(`/history?limit=${limit}`),
  exportHistory: async () => (await api.get<Blob>("/history/export", { responseType: "blob" })).data,

  research: () => get<ResearchPayload>("/research"),
  sampleCsv: async () => (await api.get<string>("/research/sample-csv", { responseType: "text" })).data,
  evaluate: async (file: File, subjects: string) => {
    const form = new FormData();
    form.append("file", file, file.name);
    form.append("test_subjects", subjects);
    return (await api.post<ResearchPayload>("/research/evaluate", form, { timeout: 120_000 })).data;
  },
  confusionImage: async () => (await api.get<Blob>("/research/confusion-matrix", { responseType: "blob" })).data,
};

/** Saves a Blob through a temporary link (CSV export). */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

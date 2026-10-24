import axios from "axios";

const TOKEN_KEY = "agrivision-token";

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
    /* storage blocked: the session lasts until reload */
  }
}

/** All calls go through the Vite proxy (/api -> backend), so no CORS and no hard-coded port. */
export const api = axios.create({ baseURL: "/api", timeout: 60_000 });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// A 401 on a signed-in call means the token expired: drop it and let AuthProvider send the user to /login.
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url = String(error?.config?.url ?? "");
    if (axios.isAxiosError(error) && error.response?.status === 401 && !url.includes("/auth/") && getToken()) {
      setToken(null);
      window.dispatchEvent(new Event("agrivision:signed-out"));
    }
    return Promise.reject(error);
  },
);

/** Turns any thrown value into a sentence for the user (API message first, then a network hint). */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (data && typeof data === "object" && typeof (data as { message?: unknown }).message === "string") {
      return (data as { message: string }).message;
    }
    if (!error.response || [502, 503, 504].includes(error.response.status))
      return "Can't reach the AgriVision API. Start the backend (run.bat) and try again.";
    if (error.response.status === 413) return "That file is too large. Use a photo under 10 MB.";
    return `The server answered ${error.response.status}.`;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function isUnauthorized(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 401;
}

/** Download a file from an authenticated endpoint and hand it to the browser. */
export async function downloadFile(path: string, fallbackName: string) {
  const res = await api.get(path, { responseType: "blob" });
  const disposition = String(res.headers["content-disposition"] ?? "");
  const name = /filename="?([^";]+)"?/.exec(disposition)?.[1] ?? fallbackName;
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/* ---------------------------------------------------------------- types */
export type Severity = "high" | "medium" | "low" | "none";

export interface User {
  id: string;
  email: string;
  phone: string;
  full_name: string;
  role: string;
  region: string;
  language: "en" | "hi" | "mr";
  crops: string[];
  created_at: string;
}

export interface Treatment {
  name: string;
  type: "chemical" | "organic" | "cultural";
  detail: string;
  cost: string;
}

export interface Disease {
  class: string;
  name: string;
  crop: string;
  disease: string;
  healthy: boolean;
  severity: Severity;
  description: string;
  symptoms: string;
  treatments: Treatment[];
  prevention: string;
  lifecycle: string;
  urgent: boolean;
}

export interface ResultSummary {
  result_id: string;
  predicted: string;
  predicted_disease: string;
  crop: string;
  healthy: boolean;
  confidence: number;
  detection_date: string;
  crop_type: string;
  severity: Severity;
  urgent: boolean;
  latency_ms: number;
  image_url: string;
  bookmarked: boolean;
}

export interface ResultDetail extends ResultSummary {
  created_at: string;
  image_size: number;
  disease_details: Disease;
  top_3_predictions: { class: string; disease: string; confidence: number; severity: Severity; healthy: boolean }[];
  engine: string;
}

export interface DashboardData {
  user: User;
  total: number;
  healthy: number;
  urgent: number;
  disease_rate: number;
  recent: ResultSummary[];
  engine: string;
}

export interface HistoryPage {
  total_count: number;
  all_count: number;
  crops: string[];
  results: ResultSummary[];
}

export interface AnalyticsData {
  total_detections: number;
  disease_distribution: Record<string, number>;
  severity: Record<Severity, number>;
  timeline: { date: string; count: number }[];
}

export interface Health {
  status: string;
  classes: number;
  engine: string;
  trained_model: boolean;
  db: string;
}

export interface DetectResponse {
  result_id: string;
  predicted_disease: string;
  confidence: number;
  severity: Severity;
  processing_time_ms: number;
  engine: string;
}

export const CROP_OPTIONS = [
  "tomato", "potato", "corn", "maize", "grape", "apple", "pepper", "orange", "peach",
  "strawberry", "squash", "cherry", "blueberry", "soybean", "raspberry", "rice", "wheat", "general",
] as const;

export const PROFILE_CROPS = ["tomato", "potato", "corn", "grape", "apple", "pepper", "rice", "wheat", "orange", "strawberry"] as const;

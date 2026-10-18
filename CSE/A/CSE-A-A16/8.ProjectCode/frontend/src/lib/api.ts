import axios from "axios";

import type {
  About,
  AppConfig,
  CollectResult,
  DatasetSummary,
  Health,
  ImageList,
  ModelInfo,
  RecognizeResult,
  TrainStatus,
} from "@/lib/types";

export const api = axios.create({ baseURL: "/api", timeout: 60_000 });

interface ApiErrorBody {
  detail?: string | { msg?: string }[];
}

/** A readable message for any API or network error. */
export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNABORTED") return "The request took too long. Please try again.";
    if (!error.response) return "Can't reach the SignSpeak server. Make sure it is running (run.bat).";
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

function frameForm(frame: Blob, extra?: Record<string, string>) {
  const form = new FormData();
  form.append("frame", frame, "frame.jpg");
  for (const [k, v] of Object.entries(extra ?? {})) form.append(k, v);
  return form;
}

export const endpoints = {
  health: () => get<Health>("/health"),
  config: () => get<AppConfig>("/config"),
  about: () => get<About>("/about"),
  dataset: () => get<DatasetSummary>("/dataset"),
  images: (cls: string, limit = 24) => get<ImageList>(`/dataset/${encodeURIComponent(cls)}/images?limit=${limit}`),
  model: () => get<ModelInfo | { trained: false }>("/model") as Promise<ModelInfo>,
  trainStatus: () => get<TrainStatus>("/train/status"),
  trainStart: async (body: { epochs: number; batch_size: number; learning_rate: number }) =>
    (await api.post<TrainStatus>("/train/start", body)).data,
  trainStop: async () => (await api.post<TrainStatus>("/train/stop")).data,
  preview: async (frame: Blob) => (await api.post<{ mask: string }>("/preview", frameForm(frame))).data,
  collect: async (cls: string, frame: Blob) =>
    (await api.post<CollectResult>(`/collect/${encodeURIComponent(cls)}`, frameForm(frame))).data,
  session: async () => (await api.post<{ session_id: string; model_loaded: boolean }>("/recognize/session")).data,
  reload: async () => (await api.post<{ model_loaded: boolean; labels: string[] }>("/recognize/reload")).data,
  recognize: async (frame: Blob, sessionId: string) =>
    (await api.post<RecognizeResult>("/recognize/frame", frameForm(frame, { session_id: sessionId }), { timeout: 15_000 })).data,
  speak: async (text: string) => (await api.post<{ spoken: boolean }>("/tts/speak", { text })).data,
};

import axios, { AxiosError } from "axios";

/** Same-origin in dev and preview: Vite proxies /api to the FastAPI backend (port 8301). */
export const api = axios.create({ baseURL: "/api", withCredentials: true });

/** Turn any thrown value into a sentence a person can act on. */
export function errorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
    if (!error.response) return "Can't reach the server. Check that the backend is running on port 8301, then try again.";
    return `The server returned an error (${error.response.status}). Please try again.`;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}

export function isUnauthorized(error: unknown) {
  return error instanceof AxiosError && error.response?.status === 401;
}

// ---- response shapes (mirror backend/main.py) ----

export interface User {
  id: number;
  username: string;
  interests: string;
}

export interface Doc {
  id: number;
  filename: string;
  subject: string;
  topics: string[];
  uploaded_at: string;
  chunk_count?: number;
}

export interface Dashboard {
  username: string;
  doc_count: number;
  query_count: number;
  quiz_attempts: number;
  performance: { subject: string; accuracy: number; attempts: number }[];
  documents: Doc[];
}

export interface Source {
  text: string;
  score: number;
  doc_id: number;
  doc_name: string;
  chunk_index: number;
}

export interface AskResult {
  id: number;
  question: string;
  answer: string;
  sources: Source[];
  created_at: string;
  llm_enabled: boolean;
}

export interface HistoryItem {
  id: number;
  question: string;
  answer: string;
  sources: string[];
  created_at: string;
}

export interface UploadResult {
  document: Doc;
  topics_count: number;
  chunks_count: number;
  warning: string | null;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  topic: string;
}

export interface Quiz {
  doc_id: number;
  doc_name: string;
  subject: string;
  questions: QuizQuestion[];
}

export interface QuizResult {
  doc_name: string;
  correct: number;
  total: number;
  score_pct: number;
  results: (QuizQuestion & { answer_index: number; selected: number | null; is_correct: boolean; subject: string })[];
}

export interface RoadmapItem {
  topic: string;
  subject: string;
  accuracy: number;
  attempts: number;
  priority: "High" | "Medium" | "Low";
}

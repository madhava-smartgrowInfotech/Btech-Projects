import axios from "axios";

/** Platform API. Vite proxies /api to the backend port (.env BACKEND_PORT). */
export const api = axios.create({ baseURL: "/api" });

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

api.interceptors.request.use((config) => {
  const token = storage()?.getItem("uh_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (e) => {
    const url = String(e.config?.url ?? "");
    if (e.response?.status === 401 && !url.includes("/auth/login")) {
      storage()?.removeItem("uh_token");
      storage()?.removeItem("uh_user");
      window.location.assign("/login");
    }
    return Promise.reject(e);
  },
);

/** What failed, in the API's own words where it gave one. */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.code === "ERR_NETWORK") return "Cannot reach the UniHealth server. Is it running?";
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d: { msg: string }) => d.msg).join(", ");
  }
  if (error instanceof Error && error.message) return error.message;
  return "Something went wrong";
}

export function statusOf(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined;
}

/** Downloads a unified record as a FHIR Bundle file. `personId` is a UniHealth id or "me". */
export async function downloadBundle(personId: string) {
  const r = await api.get<Blob>(`/records/${personId}/bundle`, { responseType: "blob" });
  const url = URL.createObjectURL(r.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `unihealth-${personId}.fhir.json`;
  a.click();
  URL.revokeObjectURL(url);
}

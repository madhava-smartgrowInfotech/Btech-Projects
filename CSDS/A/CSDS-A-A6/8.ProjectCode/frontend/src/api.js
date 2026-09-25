import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("clauseguard_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getErrorMessage(err) {
  return err?.response?.data?.detail || err?.message || "Something went wrong. Please try again.";
}

export const authApi = {
  register: (email, password) => api.post("/auth/register", { email, password }),
  login: (email, password) => api.post("/auth/login", { email, password }),
};

export const contractsApi = {
  upload: (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/contracts/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: onProgress,
      timeout: 180000,
    });
  },
  list: () => api.get("/contracts"),
  get: (id) => api.get(`/contracts/${id}`),
  getClause: (contractId, clauseId) => api.get(`/contracts/${contractId}/clauses/${clauseId}`),
  getGraph: (id) => api.get(`/contracts/${id}/graph`),
};

export const evalApi = {
  getMetrics: () => api.get("/eval/metrics"),
};

export default api;

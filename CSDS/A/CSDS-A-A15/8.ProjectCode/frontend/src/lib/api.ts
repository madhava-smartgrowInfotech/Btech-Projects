import axios from 'axios'

export const TOKEN_KEY = 'visionforge_token'

export const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface UserOut {
  id: number
  name: string
  email: string
  role: string
}

export interface TokenOut {
  access_token: string
  token_type: string
  user: UserOut
}

export interface ClassProbability {
  label: string
  display_name: string
  probability: number
}

export interface InspectionOut {
  id: number
  asset_name: string
  original_filename: string
  image_url: string
  heatmap_url: string
  defect_type: string
  display_name: string
  confidence: number
  severity: 'low' | 'medium' | 'high'
  class_probabilities: ClassProbability[]
  description: string
  root_cause_text: string
  corrective_actions: string[]
  created_at: string
}

export interface AnalyticsSummary {
  total_inspections: number
  average_confidence: number
  defect_distribution: Record<string, number>
  severity_distribution: Record<string, number>
  inspections_over_time: { date: string; count: number }[]
  model_metrics: {
    test_accuracy?: number
    best_val_accuracy?: number
    class_names?: string[]
    confusion_matrix?: number[][]
    classification_report?: Record<string, { precision: number; recall: number; 'f1-score': number; support: number }>
    history?: { epoch: number; train_loss: number; val_accuracy: number }[]
    dataset_sizes?: { train: number; val: number; test: number }
    trained_at?: string
  }
}

export const authApi = {
  register: (data: { name: string; email: string; password: string }) =>
    api.post<TokenOut>('/auth/register', data).then((r) => r.data),
  login: (data: { email: string; password: string }) =>
    api.post<TokenOut>('/auth/login', data).then((r) => r.data),
  me: () => api.get<UserOut>('/auth/me').then((r) => r.data),
}

export const inspectionsApi = {
  create: (file: File, assetName: string) => {
    const form = new FormData()
    form.append('file', file)
    return api
      .post<InspectionOut>('/inspections', form, {
        params: { asset_name: assetName },
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
  list: () => api.get<InspectionOut[]>('/inspections').then((r) => r.data),
  get: (id: number) => api.get<InspectionOut>(`/inspections/${id}`).then((r) => r.data),
  reportPath: (id: number) => `/inspections/${id}/report`,
}

export interface DefectInfo {
  display_name: string
  description: string
  likely_causes: string[]
  corrective_actions: string[]
  severity_baseline: 'low' | 'medium' | 'high'
}

export const analyticsApi = {
  summary: () => api.get<AnalyticsSummary>('/analytics/summary').then((r) => r.data),
  defectCatalog: () => api.get<Record<string, DefectInfo>>('/analytics/defect-catalog').then((r) => r.data),
}

export interface PublicModelInfo {
  defect_classes: number
  test_accuracy: number | null
  trained_at: string | null
}

export const publicApi = {
  modelInfo: () => api.get<PublicModelInfo>('/public/model-info').then((r) => r.data),
}

/** Fetches an auth-protected image and returns a local blob URL. */
export async function fetchAuthedImage(url: string): Promise<string> {
  const res = await api.get(url, { responseType: 'blob' })
  return URL.createObjectURL(res.data)
}

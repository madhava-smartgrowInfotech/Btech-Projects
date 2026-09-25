import axios from 'axios'
import type {
  HealthResponse,
  ModelInfoResponse,
  PredictionRecord,
  PredictRequest,
  StatsResponse,
} from '../types'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

export const apiClient = axios.create({ baseURL })

export async function predictGermination(payload: PredictRequest): Promise<PredictionRecord> {
  const form = new FormData()
  form.append('image', payload.image)
  form.append('soil_moisture', String(payload.soil_moisture))
  form.append('temperature', String(payload.temperature))
  form.append('humidity', String(payload.humidity))
  form.append('rainfall', String(payload.rainfall))
  form.append('soil_ph', String(payload.soil_ph))
  form.append('seed_type', payload.seed_type)

  const { data } = await apiClient.post<PredictionRecord>('/predict', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getHistory(limit = 20): Promise<PredictionRecord[]> {
  const { data } = await apiClient.get<PredictionRecord[]>('/history', { params: { limit } })
  return data
}

export async function getHistoryItem(id: string): Promise<PredictionRecord> {
  const { data } = await apiClient.get<PredictionRecord>(`/history/${id}`)
  return data
}

export async function deleteHistoryItem(id: string): Promise<void> {
  await apiClient.delete(`/history/${id}`)
}

export async function getStats(): Promise<StatsResponse> {
  const { data } = await apiClient.get<StatsResponse>('/stats')
  return data
}

export async function getModelInfo(): Promise<ModelInfoResponse> {
  const { data } = await apiClient.get<ModelInfoResponse>('/model-info')
  return data
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}

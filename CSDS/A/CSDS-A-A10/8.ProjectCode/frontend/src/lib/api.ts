import axios from 'axios'

import type {
  Bed,
  Department,
  DepartmentLoad,
  KpiSummary,
  LabTest,
  QueueBoardEntry,
  User,
  Visit,
  Vitals,
} from '@/types'

export const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('medflow_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('medflow_token')
      localStorage.removeItem('medflow_user')
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ---------- Auth ----------
export async function login(email: string, password: string) {
  const { data } = await api.post<{ access_token: string; user: User }>('/auth/login', {
    email,
    password,
  })
  return data
}

// ---------- Departments ----------
export const getDepartments = () => api.get<Department[]>('/departments').then((r) => r.data)
export const getPublicDepartments = () =>
  api.get<Department[]>('/departments/public').then((r) => r.data)
export const getDoctors = () => api.get<User[]>('/departments/staff/doctors').then((r) => r.data)

// ---------- Visits ----------
export interface CreateVisitPayload {
  patient: {
    name: string
    age: number
    gender: string
    phone?: string
    blood_group?: string
  }
  department_id: string
  chief_complaint: string
  vitals?: Vitals
}
export const createVisit = (payload: CreateVisitPayload) =>
  api.post<Visit>('/visits', payload).then((r) => r.data)

export const listVisits = (params?: { department_id?: string; status_in?: string }) =>
  api.get<Visit[]>('/visits', { params }).then((r) => r.data)

export const getVisit = (id: string) => api.get<Visit>(`/visits/${id}`).then((r) => r.data)

export const updateVisitStatus = (
  id: string,
  payload: { status: string; department_id?: string; note?: string },
) => api.patch<Visit>(`/visits/${id}/status`, payload).then((r) => r.data)

export const assignDoctor = (id: string, doctor_id: string) =>
  api.patch<Visit>(`/visits/${id}/assign-doctor`, { doctor_id }).then((r) => r.data)

export const getMovements = (id: string) => api.get(`/visits/${id}/movements`).then((r) => r.data)

// ---------- Beds ----------
export const listBeds = (department_id?: string) =>
  api.get<Bed[]>('/beds', { params: { department_id } }).then((r) => r.data)

export const updateBedStatus = (id: string, statusValue: string) =>
  api.patch<Bed>(`/beds/${id}/status`, { status: statusValue }).then((r) => r.data)

export const admitToBed = (visitId: string, bedId: string) =>
  api.post<Bed>(`/beds/visits/${visitId}/admit`, { bed_id: bedId }).then((r) => r.data)

export const releaseBed = (visitId: string) =>
  api.post<Bed>(`/beds/visits/${visitId}/release`).then((r) => r.data)

// ---------- Labs ----------
export const orderLabTest = (visit_id: string, test_name: string) =>
  api.post<LabTest>('/labs', { visit_id, test_name }).then((r) => r.data)

export const listLabTests = (status_in?: string) =>
  api.get<LabTest[]>('/labs', { params: { status_in } }).then((r) => r.data)

export const updateLabTestStatus = (id: string, statusValue: string, notes?: string) =>
  api.patch<LabTest>(`/labs/${id}/status`, { status: statusValue, notes }).then((r) => r.data)

// ---------- Dashboard ----------
export const getKpis = () => api.get<KpiSummary>('/dashboard/kpis').then((r) => r.data)
export const getDepartmentLoad = () =>
  api.get<DepartmentLoad[]>('/dashboard/department-load').then((r) => r.data)
export const getQueueBoard = () =>
  api.get<QueueBoardEntry[]>('/dashboard/queue-board').then((r) => r.data)

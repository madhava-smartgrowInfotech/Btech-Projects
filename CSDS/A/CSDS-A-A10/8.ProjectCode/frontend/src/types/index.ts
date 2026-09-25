export type Role = 'admin' | 'doctor' | 'nurse' | 'lab_tech' | 'reception'

export type DepartmentType = 'opd' | 'laboratory' | 'pharmacy' | 'ward' | 'icu' | 'emergency'

export type VisitStatus =
  | 'waiting'
  | 'in_consultation'
  | 'lab_pending'
  | 'lab_in_progress'
  | 'pharmacy'
  | 'admitted_ward'
  | 'admitted_icu'
  | 'discharged'
  | 'cancelled'

export type Priority = 'critical' | 'urgent' | 'normal'

export type BedStatus = 'available' | 'occupied' | 'cleaning' | 'reserved'

export type LabTestStatus = 'ordered' | 'scheduled' | 'in_progress' | 'completed' | 'cancelled'

export interface User {
  id: string
  name: string
  email: string
  role: Role
  specialty?: string | null
  department_id?: string | null
  avatar_color: string
}

export interface Department {
  id: string
  name: string
  code: string
  type: DepartmentType
  floor?: string | null
  avg_service_minutes: number
}

export interface Patient {
  id: string
  mrn: string
  name: string
  age: number
  gender: string
  phone?: string | null
  blood_group?: string | null
}

export interface Vitals {
  heart_rate?: number
  systolic_bp?: number
  diastolic_bp?: number
  spo2?: number
  temperature_c?: number
  respiratory_rate?: number
}

export interface Visit {
  id: string
  token_number: number
  token_code: string
  chief_complaint?: string | null
  vitals?: Vitals | null
  status: VisitStatus
  priority: Priority
  current_department_id?: string | null
  assigned_doctor_id?: string | null
  predicted_wait_minutes?: number | null
  triage_score?: number | null
  bed_id?: string | null
  created_at: string
  updated_at: string
  patient: Patient
}

export interface Bed {
  id: string
  department_id: string
  bed_number: string
  bed_type: string
  status: BedStatus
  current_visit_id?: string | null
}

export interface LabTest {
  id: string
  visit_id: string
  test_name: string
  status: LabTestStatus
  ordered_at: string
  scheduled_at?: string | null
  completed_at?: string | null
  notes?: string | null
}

export interface KpiSummary {
  patients_today: number
  active_visits: number
  avg_wait_minutes: number
  critical_cases: number
  bed_occupancy_pct: number
  icu_occupancy_pct: number
}

export interface DepartmentLoad {
  department: string
  code: string
  waiting: number
  in_progress: number
  avg_wait_minutes: number
}

export interface QueueBoardEntry {
  department: string
  code: string
  now_serving: string
  upcoming: string[]
  waiting_count: number
  avg_wait_minutes: number
}

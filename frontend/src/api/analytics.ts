import api from './client'

export interface DashboardStats {
  total_jobs_open: number           // was open_jobs
  total_applications: number
  applications_this_week: number
  avg_score_all_time: number        // was avg_ai_score
  avg_days_to_hire?: number | null
  active_bias_flags: number         // was active_bias_alerts
  hired_this_month: number
  pipeline_health: string
}

// Backend funnel returns nested stages array
export interface FunnelStage {
  stage: string
  count: number
  percentage: number
  avg_days?: number | null
}

export interface FunnelData {
  total_applied: number
  stages: FunnelStage[]
  job_id?: string | null
  job_title?: string | null
  generated_at: string
}

// Backend cohort returns nested points array
export interface CohortPoint {
  period: string        // e.g. "2026-01"
  applications: number
  hired: number
  rejected: number
  avg_score: number
  avg_days_to_hire?: number | null
}

export interface CohortData {
  points: CohortPoint[]
  department?: string | null
  granularity: string
  generated_at: string
}

export const analyticsApi = {
  getDashboard: () => api.get<{ data: DashboardStats }>('/analytics/dashboard').then(res => res.data.data),
  getFunnel: () => api.get<{ data: FunnelData }>('/analytics/funnel').then(res => res.data.data),
  getCohorts: (months = 6) => api.get<{ data: CohortData }>(`/analytics/cohorts?months=${months}`).then(res => res.data.data),
}

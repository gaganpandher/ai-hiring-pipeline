import api from './client'

export interface DashboardStats {
  open_jobs: number
  total_applications: number
  applications_this_week: number
  avg_ai_score: number
  avg_days_to_hire: number
  active_bias_alerts: number
  hired_this_month: number
  pipeline_health: string
}

export interface FunnelData {
  applied: number
  scored: number
  reviewed: number
  shortlisted: number
  hired: number
  rejected: number
  avg_days_in_stage: Record<string, number>
}

export interface CohortData {
  cohorts: {
    month: string
    total_applications: number
    hired: number
    rejected: number
    still_active: number
  }[]
}

export const analyticsApi = {
  getDashboard: () => api.get<{ data: DashboardStats }>('/analytics/dashboard').then(res => res.data.data),
  getFunnel: () => api.get<{ data: FunnelData }>('/analytics/funnel').then(res => res.data.data),
  getCohorts: (months = 6) => api.get<{ data: CohortData }>(`/analytics/cohorts?months=${months}`).then(res => res.data.data),
}

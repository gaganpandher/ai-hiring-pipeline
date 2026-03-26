import api from './client'

export type ApplicationStatus = 'pending' | 'scored' | 'reviewed' | 'shortlist' | 'rejected' | 'hired'

export interface Application {
  id: string
  job_id: string
  applicant_id: string
  resume_path: string
  cover_letter?: string
  linkedin_url?: string
  portfolio_url?: string
  status: ApplicationStatus
  submitted_at: string
  job: {
    id: string
    title: string
    department: string
  }
  applicant: {
    id: string
    full_name: string
    email: string
  }
  score?: {
    overall_score: number
    skills_score?: number
    experience_score?: number
  }
}

export interface PaginatedApplications {
  items: Application[]
  total: number
  page: number
  per_page: number
  pages: number
}

export const applicationsApi = {
  list: (params?: { job_id?: string; status?: string; page?: number; per_page?: number }) =>
    api.get<any>('/applications', { params }).then(res => ({
      items: res.data.data,
      total: res.data.total,
      page: res.data.page,
      per_page: res.data.per_page,
      pages: res.data.pages
    })),

  getById: (id: string) =>
    api.get<{ data: Application }>(`/applications/${id}`).then(res => res.data.data),

  submit: (formData: FormData) =>
    api.post<{ data: Application }>('/applications', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data.data),

  makeDecision: (id: string, status: ApplicationStatus, recruiter_notes?: string) =>
    api.patch<{ data: Application }>(`/applications/${id}/decision`, {
      status,
      recruiter_notes,
    }).then(res => res.data.data),
}

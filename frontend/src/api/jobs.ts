import api from './client'

export type JobStatus = 'draft' | 'open' | 'closed' | 'filled'
export type ExperienceLevel = 'entry' | 'mid' | 'senior' | 'lead' | 'executive'

export interface Job {
  id: string
  title: string
  department: string
  location?: string
  description: string
  requirements?: string
  salary_min?: number
  salary_max?: number
  experience_level: ExperienceLevel
  status: JobStatus
  closes_at?: string
  created_at: string
  poster: {
    id: string
    full_name: string
    email: string
  }
}

export interface PaginatedJobs {
  items: Job[]
  total: number
  page: number
  per_page: number
  pages: number
}

export const jobsApi = {
  list: (params?: { status?: string; department?: string; search?: string; page?: number; per_page?: number }) =>
    api.get<any>('/jobs', { params }).then(res => ({
      items: res.data.data,
      total: res.data.total,
      page: res.data.page,
      per_page: res.data.per_page,
      pages: res.data.pages
    })),

  getById: (id: string) =>
    api.get<{ data: Job }>(`/jobs/${id}`).then(res => res.data.data),

  create: (data: Partial<Job>) =>
    api.post<{ data: Job }>('/jobs', data).then(res => res.data.data),

  update: (id: string, data: Partial<Job>) =>
    api.patch<{ data: Job }>(`/jobs/${id}`, data).then(res => res.data.data),

  changeStatus: (id: string, new_status: JobStatus) =>
    api.patch<{ data: Job }>(`/jobs/${id}/status`, null, { params: { new_status } }).then(res => res.data.data),

  delete: (id: string) =>
    api.delete(`/jobs/${id}`).then(res => res.data),
}

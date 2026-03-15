import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '@/api/client'

export type Role = 'admin' | 'recruiter' | 'applicant'

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
}

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean

  login: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const form = new FormData()
          form.append('username', email)
          form.append('password', password)

          const { data } = await api.post('/auth/login', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })

          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)

          set({ accessToken: data.access_token, isAuthenticated: true })
          await get().fetchMe()
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, accessToken: null, isAuthenticated: false })
      },

      fetchMe: async () => {
        const { data } = await api.get('/auth/me')
        set({ user: data })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (s) => ({ accessToken: s.accessToken, isAuthenticated: s.isAuthenticated }),
    }
  )
)

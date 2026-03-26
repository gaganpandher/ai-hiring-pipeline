import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
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
  register: (data: { email: string; password: string; full_name: string; role: Role }) => Promise<void>
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
          const { data } = await api.post('/auth/login/json', {
            email,
            password
          })

          const tokens = data.data.tokens
          sessionStorage.setItem('access_token', tokens.access_token)
          sessionStorage.setItem('refresh_token', tokens.refresh_token)

          set({ accessToken: tokens.access_token, isAuthenticated: true })
          await get().fetchMe()
        } finally {
          set({ isLoading: false })
        }
      },

      register: async (data) => {
        set({ isLoading: true })
        try {
          await api.post('/auth/register', data)
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
        set({ user: null, accessToken: null, isAuthenticated: false })
      },

      fetchMe: async () => {
        const { data } = await api.get('/auth/me')
        set({ user: data.data })
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (s) => ({ accessToken: s.accessToken, isAuthenticated: s.isAuthenticated }),
    }
  )
)

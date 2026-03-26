import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore } from '@/store/authStore'
import { useNavigate, Navigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import React, { useState } from 'react'
import { Loader2, Mail, Lock, ShieldAlert } from 'lucide-react'
import clsx from 'clsx'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function AdminLogin() {
  const { login, logout, isAuthenticated, user } = useAuthStore()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  // Redirect if already logged in and admin
  if (isAuthenticated && user?.role === 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  const onSubmit = async (data: LoginForm) => {
    try {
      setIsSubmitting(true)
      await login(data.email, data.password)
      
      const loggedInUser = useAuthStore.getState().user
      if (loggedInUser?.role !== 'admin') {
        logout()
        toast.error('Unauthorized. Administrator access only.')
        return
      }

      toast.success('Admin Login verified')
      navigate('/dashboard', { replace: true })
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to authenticate admin ❌')
      logout()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Dark mode abstract background */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-rose-900/20 rounded-[100%] blur-[120px] pointer-events-none" />
      
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center flex-col items-center">
          <ShieldAlert className="h-16 w-16 text-rose-500 mb-4 animate-pulse" />
          <h2 className="text-center text-3xl font-extrabold text-white tracking-tight">
            Administrator Portal
          </h2>
          <p className="mt-2 text-center text-sm text-slate-400">
            Secure access for authorized personnel only
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-slate-900/80 backdrop-blur-xl py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-slate-800">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Admin Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="email"
                  {...register('email')}
                  className={clsx(
                    "block w-full pl-10 px-4 py-3 bg-slate-950 border text-white rounded-xl focus:ring-2 focus:ring-rose-500 focus:outline-none transition-all placeholder:text-slate-600",
                    errors.email ? "border-rose-500" : "border-slate-800 hover:border-slate-700"
                  )}
                  placeholder="admin@company.com"
                />
              </div>
              {errors.email && (
                <p className="mt-2 text-sm text-rose-400">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="password"
                  {...register('password')}
                  className={clsx(
                    "block w-full pl-10 px-4 py-3 bg-slate-950 border text-white rounded-xl focus:ring-2 focus:ring-rose-500 focus:outline-none transition-all placeholder:text-slate-600",
                    errors.password ? "border-rose-500" : "border-slate-800 hover:border-slate-700"
                  )}
                  placeholder="••••••••"
                />
              </div>
              {errors.password && (
                <p className="mt-2 text-sm text-rose-400">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-[0_0_15px_rgba(225,29,72,0.3)] text-sm font-semibold text-white bg-rose-600 hover:bg-rose-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-950 focus:ring-rose-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {isSubmitting ? (
                <Loader2 className="animate-spin h-5 w-5 text-white" />
              ) : (
                'Secure Login'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

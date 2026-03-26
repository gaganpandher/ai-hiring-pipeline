import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore } from '@/store/authStore'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import React, { useState } from 'react'
import { Loader2, Mail, Lock } from 'lucide-react'
import clsx from 'clsx'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function Login() {
  const { login, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  // Redirect if already logged in
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const onSubmit = async (data: LoginForm) => {
    try {
      setIsSubmitting(true)
      await login(data.email, data.password)
      
      const currentUser = useAuthStore.getState().user
      if (currentUser?.role === 'admin') {
        useAuthStore.getState().logout()
        toast.error('Administrators must use the Admin Portal')
        return
      }

      toast.success('Successfully logged in')
      navigate('/dashboard', { replace: true })
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to login ❌')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex">
      {/* Left abstract split screen */}
      <div className="hidden lg:flex flex-1 relative bg-[var(--bg-secondary)] overflow-hidden items-center justify-center">
        {/* Animated glowing orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/30 rounded-full mix-blend-screen filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/30 rounded-full mix-blend-screen filter blur-[128px] animate-pulse delay-1000" />
        
        <div className="z-10 text-center max-w-lg px-8">
          <div className="text-6xl mb-6 flex justify-center">🧠</div>
          <h1 className="text-4xl font-bold text-slate-900 mb-6">
            AI Hiring Pipeline
          </h1>
          <p className="text-xl text-slate-500 font-light">
            Empower your recruitment process with real-time bias detection and automated candidate scoring.
          </p>
        </div>
      </div>

      {/* Right Login Form */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:px-20 xl:px-28 relative">
        <div className="mx-auto w-full max-w-sm lg:w-96 glass-panel p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Welcome back
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Log in to access your dashboard
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="email"
                  {...register('email')}
                  className={clsx(
                    "block w-full pl-10 px-4 py-3 bg-[var(--bg-secondary)] border text-slate-800 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all placeholder:text-slate-500",
                    errors.email ? "border-rose-500" : "border-slate-200/50 hover:border-slate-300"
                  )}
                  placeholder="name@company.com"
                />
              </div>
              {errors.email && (
                <p className="mt-2 text-sm text-rose-400">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
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
                    "block w-full pl-10 px-4 py-3 bg-[var(--bg-secondary)] border text-slate-800 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all placeholder:text-slate-500",
                    errors.password ? "border-rose-500" : "border-slate-200/50 hover:border-slate-300"
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
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-slate-900 bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {isSubmitting ? (
                <Loader2 className="animate-spin h-5 w-5" />
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-500">
            Don't have an account?{' '}
            <Link to="/signup" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
              Sign Up
            </Link>
          </div>

          <div className="mt-8 text-center">
            <Link to="/admin/login" className="text-xs text-slate-400 hover:text-slate-300 transition-colors">
              Admin Portal
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

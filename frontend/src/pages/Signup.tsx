import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore, Role } from '@/store/authStore'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import React, { useState } from 'react'
import { Loader2, Mail, Lock, User, Briefcase } from 'lucide-react'
import clsx from 'clsx'

const signupSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  role: z.enum(['applicant', 'recruiter']),
})

type SignupForm = z.infer<typeof signupSchema>

export default function Signup() {
  const { register: registerAuth } = useAuthStore()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupForm>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      role: 'applicant'
    }
  })

  const onSubmit = async (data: SignupForm) => {
    try {
      setIsSubmitting(true)
      await registerAuth({ ...data, role: data.role as Role })
      toast.success('Successfully registered! Please log in.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to register ❌')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex">
      {/* Left abstract split screen */}
      <div className="hidden lg:flex flex-1 relative bg-[var(--bg-secondary)] overflow-hidden items-center justify-center">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/30 rounded-full mix-blend-screen filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/30 rounded-full mix-blend-screen filter blur-[128px] animate-pulse delay-1000" />
        
        <div className="z-10 text-center max-w-lg px-8">
          <div className="text-6xl mb-6 flex justify-center">🚀</div>
          <h1 className="text-4xl font-bold text-slate-900 mb-6">
            Join the Future of Hiring
          </h1>
          <p className="text-xl text-slate-500 font-light">
            Register for an account to streamline your recruitment process or find your next dream job.
          </p>
        </div>
      </div>

      {/* Right Signup Form */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:px-20 xl:px-28 relative">
        <div className="mx-auto w-full max-w-sm lg:w-96 glass-panel p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Create an Account
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Sign up to get started
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Full Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="text"
                  {...register('full_name')}
                  className={clsx(
                    "block w-full pl-10 px-4 py-2.5 bg-[var(--bg-secondary)] border text-slate-800 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all placeholder:text-slate-500",
                    errors.full_name ? "border-rose-500" : "border-slate-200/50 hover:border-slate-300"
                  )}
                  placeholder="Jane Doe"
                />
              </div>
              {errors.full_name && (
                <p className="mt-1 text-sm text-rose-400">{errors.full_name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="email"
                  {...register('email')}
                  className={clsx(
                    "block w-full pl-10 px-4 py-2.5 bg-[var(--bg-secondary)] border text-slate-800 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all placeholder:text-slate-500",
                    errors.email ? "border-rose-500" : "border-slate-200/50 hover:border-slate-300"
                  )}
                  placeholder="name@company.com"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-rose-400">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
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
                    "block w-full pl-10 px-4 py-2.5 bg-[var(--bg-secondary)] border text-slate-800 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all placeholder:text-slate-500",
                    errors.password ? "border-rose-500" : "border-slate-200/50 hover:border-slate-300"
                  )}
                  placeholder="••••••••"
                />
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-rose-400">{errors.password.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                I am a(n)...
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" value="applicant" {...register('role')} className="text-indigo-600 focus:ring-indigo-500" />
                  <span className="text-sm text-slate-700">Applicant</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" value="recruiter" {...register('role')} className="text-indigo-600 focus:ring-indigo-500" />
                  <span className="text-sm text-slate-700">Recruiter</span>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 mt-2 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-slate-900 bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {isSubmitting ? (
                <Loader2 className="animate-spin h-5 w-5" />
              ) : (
                'Sign Up'
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-indigo-500 hover:text-indigo-400 transition-colors">
              Log in here
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

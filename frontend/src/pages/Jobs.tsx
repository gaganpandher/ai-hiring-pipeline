import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi, Job, JobStatus } from '@/api/jobs'
import { applicationsApi } from '@/api/applications'
import { useAuthStore } from '@/store/authStore'
import { Briefcase, MapPin, DollarSign, Clock, Plus, Loader2, UploadCloud, CheckCircle2 } from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'
import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import toast from 'react-hot-toast'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

export default function Jobs() {
  const user = useAuthStore((s) => s.user)
  const isRecruiter = user?.role === 'recruiter' || user?.role === 'admin'
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [applyingToJob, setApplyingToJob] = useState<Job | null>(null)
  const queryClient = useQueryClient()

  const changeStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string, status: JobStatus }) => jobsApi.changeStatus(id, status),
    onSuccess: () => {
      toast.success('Job status updated!')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: () => toast.error('Failed to change status')
  })

  const { data, isLoading } = useQuery({
    queryKey: ['jobs', isRecruiter],
    queryFn: () => jobsApi.list({ per_page: 50, status: isRecruiter ? undefined : 'open' }),
  })

  const jobs = data?.items || []

  return (
    <>
      <div className="animate-in fade-in zoom-in-[0.98] duration-300 pb-10">
        <header className="mb-8 py-8 px-6 bg-transparent border border-slate-200 rounded-2xl flex flex-col items-center justify-center text-center  relative">
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">Job Board</h1>
        <p className="text-slate-500 max-w-2xl">
          {isRecruiter ? 'Manage open requisitions and job postings.' : 'Explore and apply to our open roles.'}
        </p>
        
        {isRecruiter && (
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-slate-900 px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg active:scale-95"
          >
            <Plus size={20} />
            Post New Job
          </button>
        )}
      </header>

      {isLoading ? (
        <div className="h-64 flex items-center justify-center">
          <Loader2 className="animate-spin text-indigo-400" size={32} />
        </div>
      ) : jobs.length === 0 ? (
        <div className="glass-panel p-12 text-center">
          <Briefcase size={48} className="mx-auto text-slate-500 mb-4" />
          <h3 className="text-lg font-medium text-slate-700">No jobs found</h3>
          <p className="text-slate-500 mt-2">There are currently no open positions.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <div key={job.id} className="glass-panel p-6 flex flex-col dynamic-hover">
              <div className="flex justify-between items-start mb-4">
                <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full text-xs font-semibold uppercase tracking-wider">
                  {job.department}
                </span>
                {isRecruiter && (
                  <select
                    value={job.status}
                    onChange={(e) => changeStatusMutation.mutate({ id: job.id, status: e.target.value as JobStatus })}
                    disabled={changeStatusMutation.isPending}
                    className={clsx(
                      "px-3 py-1.5 rounded-full text-xs font-semibold border focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer appearance-none text-center bg-transparent backdrop-blur-sm shadow-sm transition-all hover:brightness-110",
                      job.status === 'open' ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30" : 
                      job.status === 'draft' ? "bg-amber-500/10 text-amber-600 border-amber-500/30" :
                      job.status === 'closed' ? "bg-rose-500/10 text-rose-600 border-rose-500/30" :
                      "bg-indigo-500/10 text-indigo-600 border-indigo-500/30"
                    )}
                  >
                    <option value="draft">DRAFT</option>
                    <option value="open">OPEN</option>
                    <option value="closed">CLOSED</option>
                    <option value="filled">FILLED</option>
                  </select>
                )}
              </div>
              
              <h3 className="text-xl font-bold text-slate-900 mb-2 line-clamp-1">{job.title}</h3>
              
              <div className="space-y-2 mb-6 text-sm text-slate-500 flex-1">
                <div className="flex items-center gap-2">
                  <MapPin size={16} className="text-slate-500" />
                  {job.location || 'Remote'}
                </div>
                <div className="flex items-center gap-2">
                  <Briefcase size={16} className="text-slate-500" />
                  <span className="capitalize">{job.experience_level}</span>
                </div>
                {(job.salary_min || job.salary_max) && (
                  <div className="flex items-center gap-2">
                    <DollarSign size={16} className="text-slate-500" />
                    ${(job.salary_min || 0).toLocaleString()} - ${(job.salary_max || 0).toLocaleString()}
                  </div>
                )}
              </div>
              
              <p className="text-sm text-slate-700 line-clamp-2 mb-6 leading-relaxed">
                {job.description}
              </p>
              
              <div className="mt-auto pt-6 border-t border-slate-200/50 flex items-center justify-between">
                <div className="text-xs text-slate-500 flex items-center gap-1.5">
                  <Clock size={14} />
                  Posted {format(new Date(job.created_at), 'MMM d, yyyy')}
                </div>
                
                {(!isRecruiter && job.status === 'open') && (
                  <button
                    onClick={() => setApplyingToJob(job)}
                    className="text-sm font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    Apply Now →
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      </div>

      {/* Modals outside transformed context */}
      {isCreateModalOpen && (
        <CreateJobModal onClose={() => setIsCreateModalOpen(false)} />
      )}

      {applyingToJob && (
        <ApplyJobModal job={applyingToJob} onClose={() => setApplyingToJob(null)} />
      )}
    </>
  )
}

// ─── Create Job Modal ───────────────────────────────────────
const createJobSchema = z.object({
  title: z.string().min(3),
  department: z.string().min(2),
  description: z.string().min(50, 'Description must be at least 50 chars.'),
  experience_level: z.enum(['entry', 'mid', 'senior', 'lead', 'executive']),
  location: z.string().optional(),
  salary_min: z.string().optional().transform(v => v ? Number(v) : undefined),
  salary_max: z.string().optional().transform(v => v ? Number(v) : undefined),
})

function CreateJobModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const { register, handleSubmit, formState: { errors } } = useForm<z.infer<typeof createJobSchema>>({
    resolver: zodResolver(createJobSchema),
    defaultValues: { experience_level: 'mid' }
  })

  // @ts-ignore
  const onSubmit = async (data: any) => {
    setIsSubmitting(true)
    try {
      await jobsApi.create(data)
      toast.success('Job posted successfully')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      onClose()
    } catch {
      toast.error('Failed to create job')
    } finally {
      setIsSubmitting(false)
    }
  }

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[var(--bg-secondary)] border border-slate-200 rounded-2xl p-6 w-full max-w-2xl shadow-2xl overflow-y-auto max-h-[90vh]">
        <h2 className="text-2xl font-bold text-slate-900 mb-6">Post New Job</h2>
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
              <input {...register('title')} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Senior AI Engineer" />
              {errors.title && <p className="text-rose-400 text-xs mt-1">{errors.title.message as string}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Department</label>
              <input {...register('department')} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Engineering" />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea {...register('description')} rows={4} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none placeholder:text-slate-500" placeholder="Minimum 50 characters..." />
            {errors.description && <p className="text-rose-400 text-xs mt-1">{errors.description.message as string}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Experience Level</label>
              <select {...register('experience_level')} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none">
                <option value="entry">Entry</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="executive">Executive</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
              <input {...register('location')} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="Remote, NYC, etc." />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Min Salary ($)</label>
              <input type="number" {...register('salary_min')} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. 100000" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Max Salary ($)</label>
              <input type="number" {...register('salary_max')} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. 150000" />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-slate-200">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-500 hover:text-slate-900 transition-colors">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-slate-900 px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50">
              {isSubmitting && <Loader2 size={16} className="animate-spin" />}
              Create Draft
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  )
}

// ─── Apply Job Modal ─────────────────────────────────────────

function ApplyJobModal({ job, onClose }: { job: Job; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  
  const { register, handleSubmit } = useForm()

  const onSubmit = async (data: any) => {
    if (!file) {
      toast.error('Please upload your resume (PDF/Doc)')
      return
    }

    setIsSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('job_id', job.id)
      formData.append('resume', file)
      if (data.cover_letter) formData.append('cover_letter', data.cover_letter)
      if (data.linkedin_url) formData.append('linkedin_url', data.linkedin_url)
      
      await applicationsApi.submit(formData)
      toast.success('Application submitted! AI is now reviewing your resume.')
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      onClose()
      
      // Navigate isn't easily accessible here without useHook, but user knows to check 'Applications' tab
    } catch {
      toast.error('Failed to submit application')
    } finally {
      setIsSubmitting(false)
    }
  }

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[var(--bg-secondary)] border border-slate-200 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        <div className="p-6 border-b border-slate-200 bg-slate-100/30">
          <h2 className="text-xl font-bold text-slate-900 mb-1">Apply for {job.title}</h2>
          <p className="text-sm text-slate-500">{job.department} • {job.location || 'Remote'}</p>
        </div>
        
        <div className="p-6 overflow-y-auto">
          <form id="applyForm" onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Resume (Required)</label>
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-xl cursor-pointer bg-slate-100/50 hover:bg-slate-100 hover:border-indigo-400 transition-all">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  {file ? (
                    <>
                      <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
                      <p className="text-sm text-slate-700 font-medium">{file.name}</p>
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-8 h-8 text-slate-500 mb-2" />
                      <p className="text-sm text-slate-500"><span className="font-semibold text-indigo-400">Click to upload</span> or drag and drop</p>
                      <p className="text-xs text-slate-500 mt-1">PDF or DOCX (MAX. 5MB)</p>
                    </>
                  )}
                </div>
                <input type="file" className="hidden" accept=".pdf,.doc,.docx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">LinkedIn Profile</label>
              <input {...register('linkedin_url')} type="url" className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="https://linkedin.com/in/..." />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Cover Letter (Optional)</label>
              <textarea {...register('cover_letter')} rows={3} className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="Why are you a good fit?" />
            </div>
          </form>
        </div>

        <div className="p-6 border-t border-slate-200 bg-slate-100/30 flex justify-end gap-3 mt-auto">
          <button type="button" onClick={onClose} className="px-4 py-2 text-slate-500 hover:text-slate-900 transition-colors">Cancel</button>
          <button form="applyForm" type="submit" disabled={isSubmitting || !file} className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-slate-900 px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50">
            {isSubmitting && <Loader2 size={16} className="animate-spin" />}
            Submit Application
          </button>
        </div>

      </div>
    </div>,
    document.body
  )
}

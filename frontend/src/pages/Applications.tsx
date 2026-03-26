import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { applicationsApi, Application, ApplicationStatus } from '@/api/applications'
import { useAuthStore } from '@/store/authStore'
import { FileText, Loader2, CheckCircle, XCircle, Clock, Link as LinkIcon, ExternalLink } from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import React, { useState } from 'react'
import { Link } from 'react-router-dom'

export default function Applications() {
  const user = useAuthStore((s) => s.user)
  const isRecruiter = user?.role === 'recruiter' || user?.role === 'admin'
  const queryClient = useQueryClient()

  const [page, setPage] = useState(1)
  const [selectedStatus, setSelectedStatus] = useState<string>('')

  const { data, isLoading } = useQuery({
    queryKey: ['applications', page, selectedStatus],
    queryFn: () => applicationsApi.list({ page, per_page: 15, status: selectedStatus || undefined }),
  })

  const decisionMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ApplicationStatus }) => applicationsApi.makeDecision(id, status),
    onSuccess: () => {
      toast.success('Decision recorded')
      queryClient.invalidateQueries({ queryKey: ['applications'] })
    },
    onError: () => toast.error('Failed to record decision')
  })

  const handleDecision = (id: string, status: ApplicationStatus) => {
    decisionMutation.mutate({ id, status })
  }

  const apps = data?.items || []

  return (
    <div className="animate-in fade-in zoom-in-[0.98] duration-300 pb-10">
      <header className="mb-8 py-8 px-6 bg-transparent border border-slate-200 rounded-2xl flex flex-col items-center justify-center text-center  relative">
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">Applications</h1>
        <p className="text-slate-500 max-w-2xl">
          {isRecruiter ? 'Review and manage candidate applications.' : 'Track your submitted applications.'}
        </p>
        
        {isRecruiter && (
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-[var(--bg-secondary)] border border-slate-200 text-slate-800 rounded-xl px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="scored">Scored</option>
            <option value="shortlist">Shortlisted</option>
            <option value="rejected">Rejected</option>
            <option value="hired">Hired</option>
          </select>
        )}
      </header>

      {isLoading ? (
        <div className="h-64 flex items-center justify-center">
          <Loader2 className="animate-spin text-indigo-400" size={32} />
        </div>
      ) : apps.length === 0 ? (
        <div className="glass-panel p-12 text-center">
          <FileText size={48} className="mx-auto text-slate-500 mb-4" />
          <h3 className="text-lg font-medium text-slate-700">No applications found</h3>
          <p className="text-slate-500 mt-2">Check back later or adjust your filters.</p>
        </div>
      ) : (
        <div className="glass-panel overflow-hidden border border-slate-200/50">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/50 text-slate-500 text-sm uppercase tracking-wider">
                  <th className="px-6 py-4 font-medium">Candidate</th>
                  <th className="px-6 py-4 font-medium">Position</th>
                  <th className="px-6 py-4 font-medium">AI Score</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium">Date Applied</th>
                  {isRecruiter && <th className="px-6 py-4 font-medium text-right">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50 text-slate-700">
                {apps.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-100/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{app.applicant.full_name}</div>
                      <div className="text-sm text-slate-500">{app.applicant.email}</div>
                      {(app.linkedin_url || app.portfolio_url) && (
                        <div className="flex gap-3 mt-2">
                          {app.linkedin_url && (
                            <a href={app.linkedin_url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 text-xs">
                              <LinkIcon size={12} /> LinkedIn
                            </a>
                          )}
                          {app.portfolio_url && (
                            <a href={app.portfolio_url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 text-xs">
                              <ExternalLink size={12} /> Portfolio
                            </a>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-800">{app.job.title}</div>
                      <div className="text-sm text-slate-500">{app.job.department}</div>
                    </td>
                    <td className="px-6 py-4">
                      {app.score ? (
                        <div className="flex items-center gap-2">
                          <span className={clsx(
                            "text-lg font-bold",
                            app.score.overall_score >= 80 ? "text-emerald-400" :
                            app.score.overall_score >= 60 ? "text-yellow-400" : "text-rose-400"
                          )}>
                            {app.score.overall_score}
                          </span>
                          <span className="text-xs text-slate-500">/ 100</span>
                        </div>
                      ) : (
                        <span className="text-slate-500 text-sm flex items-center gap-1">
                          <Clock size={14} /> Pending Scan
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {format(new Date(app.submitted_at), 'MMM d, yyyy')}
                    </td>
                    {isRecruiter && (
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleDecision(app.id, 'shortlist')}
                            disabled={app.status === 'shortlist' || decisionMutation.isPending}
                            className="p-2 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded-lg transition-colors disabled:opacity-50"
                            title="Shortlist"
                          >
                            <CheckCircle size={18} />
                          </button>
                          <button
                            onClick={() => handleDecision(app.id, 'rejected')}
                            disabled={app.status === 'rejected' || decisionMutation.isPending}
                            className="p-2 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 rounded-lg transition-colors disabled:opacity-50"
                            title="Reject"
                          >
                            <XCircle size={18} />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination Controls */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 bg-slate-100/20 border-t border-slate-200/50">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-[var(--bg-secondary)] border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-700/50 disabled:opacity-50 transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-slate-500">
                Page {page} of {data.pages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="px-4 py-2 bg-[var(--bg-secondary)] border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-700/50 disabled:opacity-50 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: ApplicationStatus }) {
  const map: Record<ApplicationStatus, { label: string, color: string }> = {
    pending: { label: 'Pending', color: 'bg-slate-500/10 text-slate-500 border-slate-500/20' },
    scored: { label: 'Scored', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
    reviewed: { label: 'Reviewed', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
    shortlist: { label: 'Shortlisted', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
    hired: { label: 'Hired', color: 'bg-violet-500/10 text-violet-400 border-violet-500/20' },
    rejected: { label: 'Rejected', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
  }
  
  const { label, color } = map[status] || map.pending
  return (
    <span className={clsx("px-2.5 py-1 text-xs font-semibold rounded-full border", color)}>
      {label}
    </span>
  )
}

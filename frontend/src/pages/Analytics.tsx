import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import { jobsApi } from '@/api/jobs'
import { useAuthStore } from '@/store/authStore'
import { ShieldAlert, Info, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'
import React, { useState } from 'react'
import api from '@/api/client'

export default function Analytics() {
  const user = useAuthStore(s => s.user)
  // Only recruiters and admins should access此 page, protected by ProtectedRoute
  
  // List all open jobs to select one for the bias report
  const { data: jobsData } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsApi.list({ per_page: 50 })
  })

  const [selectedJobId, setSelectedJobId] = useState<string>('')

  return (
    <div className="animate-in fade-in zoom-in-[0.98] duration-300 pb-10">
      <header className="mb-8 py-8 px-4 bg-transparent border border-slate-200 rounded-2xl text-center flex flex-col items-center justify-center  w-full">
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">Bias Reporting</h1>
        <p className="text-slate-500 max-w-2xl mx-auto">
          Our real-time AI engine flags statistically significant demographic disparities traversing the pipeline out of standard deviations. Ensure equitable hiring across departments.
        </p>
      </header>

      <div className="glass-panel p-6 mb-8 max-w-md">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Select Requisition to Audit
        </label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full bg-[var(--bg-secondary)] border border-slate-200 text-slate-800 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none"
        >
          <option value="">-- Choose a job posting --</option>
          {jobsData?.items?.map(job => (
            <option key={job.id} value={job.id}>{job.title} ({job.department})</option>
          ))}
        </select>
      </div>

      {selectedJobId ? (
         <BiasReportView jobId={selectedJobId} />
      ) : (
        <div className="glass-panel p-12 text-center max-w-4xl border-dashed border-slate-200">
          <ShieldAlert className="mx-auto text-slate-500 mb-4 h-12 w-12" />
          <h3 className="text-lg font-medium text-slate-700">No Job Selected</h3>
          <p className="text-slate-500 mt-2 text-sm">Select a job from the dropdown above to run a demographic disparity audit.</p>
        </div>
      )}
    </div>
  )
}

function BiasReportView({ jobId }: { jobId: string }) {
  const { data: reportWrapper, isLoading } = useQuery({
    queryKey: ['biasReport', jobId],
    queryFn: () => api.get(`/analytics/bias/${jobId}`).then((res: any) => res.data)
  })

  if (isLoading) return <div className="h-48 flex items-center justify-center"><Loader2 className="animate-spin text-indigo-400 h-8 w-8" /></div>

  const report = reportWrapper?.data

  if (!report || report.sample_size === 0) {
    return (
      <div className="glass-panel p-6 bg-slate-100/20 max-w-4xl">
        <div className="flex gap-4">
          <Info className="text-blue-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-slate-900">Insufficient Data</h4>
            <p className="text-sm text-slate-500 mt-1">This job requires more applications (min 5) to generate a statistically significant bias report.</p>
          </div>
        </div>
      </div>
    )
  }

  const isFlagged = report.is_flagged
  const sampleSize = report.sample_size
  const dataPoints = report.data_points || []
  const biasType = report.bias_type || 'demographic'

  return (
    <div className="max-w-4xl space-y-6">
      <div className={`glass-panel p-6 border-l-4 ${isFlagged ? 'border-l-rose-500 bg-rose-500/5' : 'border-l-emerald-500 bg-emerald-500/5'}`}>
        <div className="flex items-start gap-4">
          {isFlagged ? <AlertTriangle className="text-rose-500 shrink-0" size={28} /> : <CheckCircle className="text-emerald-500 shrink-0" size={28} />}
          <div>
            <h2 className="text-xl font-bold text-slate-900">{isFlagged ? 'Bias Warning Flagged' : 'Pipeline appears equitable'}</h2>
            <p className="text-slate-500 mt-1 text-sm">
              {isFlagged 
                ? `Statistical anomalies detected. The system has flagged potential ${biasType} bias.`
                : `No statistical bias detected across ${sampleSize} applications based on standard deviation limits.`}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dataPoints.map((dp: any) => (
          <div key={dp.group} className="glass-panel p-5">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4 border-b border-slate-200/50 pb-2">{dp.group}</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">Applications</span>
                <span className="text-slate-900 font-medium">{dp.total_reviewed}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">Acceptance Rate</span>
                <span className={`text-sm font-bold ${dp.acceptance_rate < 0.2 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {(dp.acceptance_rate * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

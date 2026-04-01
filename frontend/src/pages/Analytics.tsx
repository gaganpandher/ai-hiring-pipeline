import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobs'
import { useAuthStore } from '@/store/authStore'
import {
  ShieldAlert, Info, AlertTriangle, CheckCircle,
  Loader2, Users, TrendingUp, Percent, Brain
} from 'lucide-react'
import React, { useState } from 'react'
import api from '@/api/client'
import clsx from 'clsx'

export default function Analytics() {
  useAuthStore(s => s.user)

  const { data: jobsData } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsApi.list({ per_page: 100 })
  })

  const [selectedJobId, setSelectedJobId] = useState<string>('')

  return (
    <div className="animate-in fade-in zoom-in-[0.98] duration-300 pb-10">
      <header className="mb-8 py-8 px-4 bg-transparent border border-slate-200 rounded-2xl text-center flex flex-col items-center justify-center w-full">
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">Bias Reporting</h1>
        <p className="text-slate-500 max-w-2xl mx-auto">
          Real-time AI-powered analysis of demographic disparities across your hiring pipeline. Select a job to audit acceptance rates and AI scores by group.
        </p>
      </header>

      {/* Job selector */}
      <div className="glass-panel p-6 mb-8 max-w-lg">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Select Requisition to Audit
        </label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full bg-white border border-slate-200 text-slate-800 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none"
        >
          <option value="">-- Choose a job posting --</option>
          {jobsData?.items?.map(job => (
            <option key={job.id} value={job.id}>
              {job.title} · {job.department}
            </option>
          ))}
        </select>
      </div>

      {selectedJobId ? (
        <BiasReportView jobId={selectedJobId} />
      ) : (
        <div className="glass-panel p-12 text-center border-dashed border-slate-200">
          <ShieldAlert className="mx-auto text-slate-400 mb-4 h-12 w-12" />
          <h3 className="text-lg font-semibold text-slate-700">No Job Selected</h3>
          <p className="text-slate-500 mt-2 text-sm max-w-sm mx-auto">
            Select a job from the dropdown above to generate a demographic disparity audit.
          </p>
        </div>
      )}
    </div>
  )
}

// ─── Bias Report View ─────────────────────────────────────────────────────────
function BiasReportView({ jobId }: { jobId: string }) {
  const { data: reportWrapper, isLoading } = useQuery({
    queryKey: ['biasReport', jobId],
    queryFn: () => api.get(`/analytics/bias/${jobId}`).then((res: any) => res.data),
    retry: 1,
  })

  if (isLoading) return (
    <div className="h-48 flex items-center justify-center">
      <Loader2 className="animate-spin text-indigo-400 h-8 w-8" />
    </div>
  )

  const report = reportWrapper?.data

  // No data at all (API error or no response)
  if (!report) return (
    <div className="glass-panel p-6 border-l-4 border-l-amber-400 bg-amber-50">
      <div className="flex gap-3 items-start">
        <Info className="text-amber-500 shrink-0 mt-0.5" size={20} />
        <div>
          <h4 className="font-semibold text-slate-900">Could not load bias report</h4>
          <p className="text-sm text-slate-500 mt-1">There was an error fetching bias data for this job.</p>
        </div>
      </div>
    </div>
  )

  const { is_flagged, sample_size, data_points = [], bias_type, job_title, p_value, severity } = report

  // Not enough reviewed applications
  if (sample_size === 0) return (
    <div className="glass-panel p-6 border-l-4 border-l-blue-400 bg-blue-50">
      <div className="flex gap-3 items-start">
        <Info className="text-blue-500 shrink-0 mt-0.5" size={20} />
        <div>
          <h4 className="font-semibold text-slate-900">Insufficient Data</h4>
          <p className="text-sm text-slate-500 mt-1">
            This report requires applicants to be moved through the pipeline (reviewed, shortlisted, hired, or rejected).
            Applications must be actioned by a recruiter before they appear here.
          </p>
        </div>
      </div>
    </div>
  )

  // Max acceptance rate for relative bar scaling
  const maxRate = Math.max(...data_points.map((d: any) => d.acceptance_rate), 0.01)

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div className={clsx(
        'glass-panel p-5 border-l-4',
        is_flagged ? 'border-l-rose-500 bg-rose-50' : 'border-l-emerald-500 bg-emerald-50'
      )}>
        <div className="flex items-start gap-4">
          {is_flagged
            ? <AlertTriangle className="text-rose-500 shrink-0" size={26} />
            : <CheckCircle className="text-emerald-500 shrink-0" size={26} />
          }
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-xl font-bold text-slate-900">
                {is_flagged ? '⚠️ Bias Warning Detected' : '✅ Pipeline Appears Equitable'}
              </h2>
              {severity && (
                <span className={clsx(
                  'text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider',
                  severity === 'high' ? 'bg-rose-200 text-rose-800' :
                  severity === 'medium' ? 'bg-amber-200 text-amber-800' :
                  'bg-slate-200 text-slate-700'
                )}>
                  {severity} severity
                </span>
              )}
            </div>
            <p className="text-slate-600 mt-1 text-sm">
              {is_flagged
                ? `Statistically significant ${bias_type ?? 'demographic'} disparity detected across ${sample_size} reviewed applications.`
                : `No significant bias detected across ${sample_size} reviewed applications for "${job_title}".`}
            </p>
            {p_value != null && (
              <p className="text-xs text-slate-400 mt-1">p-value: {p_value.toFixed(4)}</p>
            )}
          </div>
        </div>
      </div>

      {/* Summary Stat Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Reviewed', value: sample_size, icon: Users, color: 'text-indigo-600 bg-indigo-100' },
          { label: 'Groups Detected', value: data_points.length, icon: Brain, color: 'text-violet-600 bg-violet-100' },
          { label: 'Bias Type', value: (bias_type ?? 'gender'), icon: ShieldAlert, color: 'text-amber-600 bg-amber-100' },
          { label: 'Status', value: is_flagged ? 'Flagged' : 'Clean', icon: is_flagged ? AlertTriangle : CheckCircle, color: is_flagged ? 'text-rose-600 bg-rose-100' : 'text-emerald-600 bg-emerald-100' },
        ].map(s => (
          <div key={s.label} className="glass-panel p-4 flex items-center gap-3">
            <div className={clsx('p-2 rounded-lg', s.color.split(' ')[1])}>
              <s.icon size={18} className={s.color.split(' ')[0]} />
            </div>
            <div>
              <div className="text-lg font-bold text-slate-900 capitalize">{s.value}</div>
              <div className="text-xs text-slate-500">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Group Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {data_points.map((dp: any) => {
          const rate = dp.acceptance_rate ?? 0
          const barWidth = maxRate > 0 ? (rate / maxRate) * 100 : 0
          const rateColor = rate < 0.15 ? 'bg-rose-500' : rate < 0.35 ? 'bg-amber-500' : 'bg-emerald-500'

          return (
            <div key={dp.group} className="glass-panel p-5 space-y-4">
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200/60 pb-2 capitalize">
                {dp.group}
              </h3>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 flex items-center gap-1.5"><Users size={13} /> Total Reviewed</span>
                  <span className="font-semibold text-slate-900">{dp.total_reviewed}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 flex items-center gap-1.5"><CheckCircle size={13} /> Accepted</span>
                  <span className="font-semibold text-slate-900">{dp.total_accepted}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 flex items-center gap-1.5"><Brain size={13} /> Avg AI Score</span>
                  <span className={clsx(
                    'font-bold',
                    dp.avg_score >= 70 ? 'text-emerald-600' :
                    dp.avg_score >= 50 ? 'text-amber-600' : 'text-rose-500'
                  )}>
                    {dp.avg_score != null ? dp.avg_score.toFixed(1) : '—'}
                  </span>
                </div>
              </div>

              {/* Acceptance Rate Bar */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-xs text-slate-500 flex items-center gap-1"><Percent size={11} /> Acceptance Rate</span>
                  <span className={clsx(
                    'text-sm font-bold',
                    rate < 0.15 ? 'text-rose-500' : rate < 0.35 ? 'text-amber-500' : 'text-emerald-600'
                  )}>
                    {(rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={clsx('h-full rounded-full transition-all duration-500', rateColor)}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Comparison Table */}
      {data_points.length > 1 && (
        <div className="glass-panel overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200/60">
            <h3 className="text-base font-semibold text-slate-800">Side-by-Side Comparison</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50/70 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-medium">Group</th>
                  <th className="px-6 py-3 font-medium text-right">Reviewed</th>
                  <th className="px-6 py-3 font-medium text-right">Accepted</th>
                  <th className="px-6 py-3 font-medium text-right">Acceptance Rate</th>
                  <th className="px-6 py-3 font-medium text-right">Avg AI Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data_points.map((dp: any) => (
                  <tr key={dp.group} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3 font-medium text-slate-800 capitalize">{dp.group}</td>
                    <td className="px-6 py-3 text-right text-slate-700">{dp.total_reviewed}</td>
                    <td className="px-6 py-3 text-right text-slate-700">{dp.total_accepted}</td>
                    <td className={clsx(
                      'px-6 py-3 text-right font-bold',
                      dp.acceptance_rate < 0.15 ? 'text-rose-500' :
                      dp.acceptance_rate < 0.35 ? 'text-amber-500' : 'text-emerald-600'
                    )}>
                      {(dp.acceptance_rate * 100).toFixed(1)}%
                    </td>
                    <td className={clsx(
                      'px-6 py-3 text-right font-semibold',
                      dp.avg_score >= 70 ? 'text-emerald-600' :
                      dp.avg_score >= 50 ? 'text-amber-600' : 'text-rose-500'
                    )}>
                      {dp.avg_score != null ? dp.avg_score.toFixed(1) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-xs text-slate-400 max-w-2xl">
        ℹ️ Group classification is based on name-pattern proxies and is intended as a statistical indicator only.
        It does not represent actual demographic data. Always consult HR and legal before taking action on these results.
      </p>
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import { applicationsApi, Application } from '@/api/applications'
import { useAuthStore } from '@/store/authStore'
import { Loader2, Briefcase, Clock, CheckCircle2, XCircle, Star, TrendingUp } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import React from 'react'
import { format } from 'date-fns'
import clsx from 'clsx'

import FunnelChart from '@/components/FunnelChart'
import BiasAlerts from '@/components/BiasAlerts'
import ScoreCards from '@/components/ScoreCards'

// ─── Applicant Dashboard ──────────────────────────────────────────────────────
function ApplicantDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['applications', 'mine'],
    queryFn: () => applicationsApi.list({ per_page: 100 }),
  })

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
      </div>
    )
  }

  const apps: Application[] = data?.items || []
  const total = apps.length
  const pending  = apps.filter(a => a.status === 'pending').length
  const scored   = apps.filter(a => a.status === 'scored').length
  const shortlisted = apps.filter(a => a.status === 'shortlist').length
  const hired    = apps.filter(a => a.status === 'hired').length
  const rejected = apps.filter(a => a.status === 'rejected').length

  const scoredApps = apps.filter(a => a.score?.overall_score != null)
  const avgScore = scoredApps.length
    ? Math.round(scoredApps.reduce((s, a) => s + (a.score?.overall_score ?? 0), 0) / scoredApps.length)
    : null

  const statCards = [
    { label: 'Total Applications', value: total, icon: Briefcase, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
    { label: 'Pending Review', value: pending + scored, icon: Clock, color: 'text-amber-500', bg: 'bg-amber-500/10' },
    { label: 'Shortlisted', value: shortlisted, icon: Star, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { label: 'Avg AI Score', value: avgScore != null ? `${avgScore}/100` : '—', icon: TrendingUp, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  ]

  const statusLabel: Record<string, string> = {
    pending: 'Pending',
    scored: 'AI Scored',
    reviewed: 'Under Review',
    shortlist: 'Shortlisted',
    hired: 'Hired 🎉',
    rejected: 'Rejected',
  }
  const statusColor: Record<string, string> = {
    pending: 'bg-slate-100 text-slate-600',
    scored: 'bg-indigo-100 text-indigo-700',
    reviewed: 'bg-amber-100 text-amber-700',
    shortlist: 'bg-emerald-100 text-emerald-700',
    hired: 'bg-emerald-200 text-emerald-800 font-bold',
    rejected: 'bg-rose-100 text-rose-700',
  }

  return (
    <div className="animate-in fade-in zoom-in-[0.98] duration-300 pb-10 space-y-8">
      <header className="mb-2">
        <h1 className="text-3xl font-bold text-slate-900 mb-1">My Dashboard</h1>
        <p className="text-slate-500">Track the status of all your job applications in one place.</p>
      </header>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(card => (
          <div key={card.label} className="glass-panel p-5 flex items-center gap-4">
            <div className={clsx('p-3 rounded-xl', card.bg)}>
              <card.icon size={22} className={card.color} />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{card.value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{card.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Applications Table */}
      {apps.length === 0 ? (
        <div className="glass-panel p-12 text-center">
          <Briefcase size={48} className="mx-auto text-slate-400 mb-4" />
          <h3 className="text-lg font-semibold text-slate-700">No applications yet</h3>
          <p className="text-slate-500 mt-2">Head to the Job Board to explore and apply to open roles.</p>
        </div>
      ) : (
        <div className="glass-panel overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200/60">
            <h2 className="text-base font-semibold text-slate-800">Your Applications</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50/70 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-medium">Job</th>
                  <th className="px-6 py-3 font-medium">Job ID</th>
                  <th className="px-6 py-3 font-medium">AI Score</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Applied On</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {apps.map((app: Application) => (
                  <tr key={app.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{app.job?.title ?? '—'}</div>
                      <div className="text-xs text-slate-500">{app.job?.department ?? ''}</div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-500">{app.job?.id ?? '—'}</td>
                    <td className="px-6 py-4">
                      {app.score?.overall_score != null ? (
                        <span className={clsx(
                          "text-base font-bold",
                          app.score.overall_score >= 80 ? "text-emerald-500" :
                          app.score.overall_score >= 60 ? "text-amber-500" : "text-rose-500"
                        )}>
                          {app.score.overall_score}<span className="text-xs text-slate-400 font-normal">/100</span>
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs flex items-center gap-1">
                          <Clock size={12} /> Pending Scan
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={clsx("px-2.5 py-1 rounded-full text-xs font-medium", statusColor[app.status] ?? 'bg-slate-100 text-slate-600')}>
                        {statusLabel[app.status] ?? app.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500 text-xs">
                      {format(new Date(app.submitted_at), 'MMM d, yyyy')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Outcome Summary */}
      {total > 0 && (
        <div className="glass-panel p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Outcome Summary</h3>
          <div className="flex flex-wrap gap-4 text-sm">
            {[
              { label: 'Hired', count: hired, color: 'text-emerald-600' },
              { label: 'Shortlisted', count: shortlisted, color: 'text-indigo-600' },
              { label: 'Rejected', count: rejected, color: 'text-rose-500' },
              { label: 'Pending', count: pending + scored, color: 'text-amber-600' },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2">
                <span className={clsx("font-bold text-xl", item.color)}>{item.count}</span>
                <span className="text-slate-500">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Recruiter / Admin Dashboard ─────────────────────────────────────────────
function RecruiterDashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: analyticsApi.getDashboard,
  })

  const { data: funnel, isLoading: funnelLoading } = useQuery({
    queryKey: ['dashboardFunnel'],
    queryFn: analyticsApi.getFunnel,
  })

  const { data: cohortPayload, isLoading: cohortLoading } = useQuery({
    queryKey: ['dashboardCohorts'],
    queryFn: () => analyticsApi.getCohorts(6),
  })

  if (statsLoading || funnelLoading || cohortLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
      </div>
    )
  }

  // Backend returns { points: [{ period, applications, hired, rejected, avg_score }] }
  const cohorts = (cohortPayload?.points || []).map(p => ({
    month: p.period,
    total_applications: p.applications,
    hired: p.hired,
    rejected: p.rejected,
  }))

  return (
    <div className="animate-in fade-in zoom-in-[0.98] duration-300 pb-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Overview</h1>
        <p className="text-slate-500">Track your recruitment pipeline performance and structural metrics.</p>
      </header>

      <ScoreCards stats={stats} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 glass-panel p-6 bg-white">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Application Trend</h2>
              <p className="text-sm text-slate-500">Monthly applicant volume over 6 months</p>
            </div>
            <BiasAlerts count={stats?.active_bias_flags} />
          </div>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cohorts} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                  itemStyle={{ color: '#0f172a' }}
                />
                <Area type="monotone" dataKey="total_applications" stroke="#818cf8" strokeWidth={3} fillOpacity={1} fill="url(#colorTotal)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <FunnelChart data={funnel || null} />
      </div>
    </div>
  )
}

// ─── Root Dashboard — role-aware ─────────────────────────────────────────────
export default function Dashboard() {
  const user = useAuthStore(s => s.user)
  const isRecruiter = user?.role === 'recruiter' || user?.role === 'admin'
  return isRecruiter ? <RecruiterDashboard /> : <ApplicantDashboard />
}

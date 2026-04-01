import React from 'react'
import clsx from 'clsx'
import { Briefcase, Users, Sparkles, Clock, LucideIcon } from 'lucide-react'

interface ScoreCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend: string
  color: 'indigo' | 'blue' | 'violet' | 'emerald'
}

export function ScoreCard({ title, value, icon: Icon, trend, color }: ScoreCardProps) {
  const colorMap: Record<string, string> = {
    indigo: 'text-indigo-600 bg-indigo-100 border-indigo-200',
    blue: 'text-blue-600 bg-blue-100 border-blue-200',
    violet: 'text-violet-600 bg-violet-100 border-violet-200',
    emerald: 'text-emerald-600 bg-emerald-100 border-emerald-200',
  }
  const colorClass = colorMap[color]

  return (
    <div className="glass-panel p-5 relative overflow-hidden group dynamic-hover bg-white">
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div className={clsx("p-2 rounded-lg border", colorClass)}>
          <Icon size={20} />
        </div>
        <span className="text-xs font-medium text-emerald-600 bg-emerald-100 px-2 py-1 rounded-full">
          {trend}
        </span>
      </div>
      <div className="relative z-10">
        <h3 className="text-sm font-medium text-slate-500 mb-1">{title}</h3>
        <p className="text-3xl font-bold text-slate-900 tracking-tight">{value}</p>
      </div>
      {/* Decorative gradient orb */}
      <div className={clsx("absolute -right-6 -bottom-6 w-24 h-24 rounded-full blur-2xl opacity-40 group-hover:opacity-60 transition-opacity", colorClass.split(' ')[0].replace('text-', 'bg-'))} />
    </div>
  )
}

interface ScoreCardsContainerProps {
  stats: {
    total_jobs_open: number
    total_applications: number
    applications_this_week: number
    avg_score_all_time: number
    avg_days_to_hire?: number | null
  } | undefined
}

export default function ScoreCards({ stats }: ScoreCardsContainerProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
      <ScoreCard
        title="Open Jobs"
        value={stats?.total_jobs_open ?? 0}
        icon={Briefcase}
        trend="+2 this week"
        color="indigo"
      />
      <ScoreCard
        title="Total Applications"
        value={stats?.total_applications ?? 0}
        icon={Users}
        trend={`+${stats?.applications_this_week ?? 0} this week`}
        color="blue"
      />
      <ScoreCard
        title="Average AI Score"
        value={stats?.avg_score_all_time ? stats.avg_score_all_time.toFixed(1) : 0}
        icon={Sparkles}
        trend="Top 15% threshold"
        color="violet"
      />
      <ScoreCard
        title="Avg Days to Hire"
        value={stats?.avg_days_to_hire ? stats.avg_days_to_hire.toFixed(1) : '—'}
        icon={Clock}
        trend="-2.4 days vs prev"
        color="emerald"
      />
    </div>
  )
}

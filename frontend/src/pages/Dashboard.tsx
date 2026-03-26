import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import { Loader2 } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import React from 'react'

import FunnelChart from '@/components/FunnelChart'
import BiasAlerts from '@/components/BiasAlerts'
import ScoreCards from '@/components/ScoreCards'

export default function Dashboard() {
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

  const cohorts = cohortPayload?.cohorts || []

  return (
    <div className="animate-in fade-in zoom-in-[0.98] duration-300 pb-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Overview</h1>
        <p className="text-slate-500">Track your recruitment pipeline performance and structural metrics.</p>
      </header>

      {/* KPI Cards */}
      <ScoreCards stats={stats} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main Chart Area */}
        <div className="xl:col-span-2 glass-panel p-6 bg-white">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Application Trend</h2>
              <p className="text-sm text-slate-500">Monthly applicant volume over 6 months</p>
            </div>
            <BiasAlerts count={stats?.active_bias_alerts} />
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

        {/* Funnel Chart Area */}
        <FunnelChart data={funnel || null} />
      </div>
    </div>
  )
}

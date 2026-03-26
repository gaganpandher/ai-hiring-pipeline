import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface FunnelChartProps {
  data: {
    applied: number
    scored: number
    reviewed: number
    shortlisted: number
    hired: number
  } | null
}

export default function FunnelChart({ data }: FunnelChartProps) {
  const chartData = data
    ? [
        { name: 'Applied', value: data.applied },
        { name: 'Scored', value: data.scored },
        { name: 'Reviewed', value: data.reviewed },
        { name: 'Shortlisted', value: data.shortlisted },
        { name: 'Hired', value: data.hired },
      ]
    : []

  return (
    <div className="glass-panel p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-900">Conversion Funnel</h2>
        <p className="text-sm text-slate-500">Current pipeline stages</p>
      </div>
      <div className="h-80 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 30, left: 20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
            <XAxis type="number" hide />
            <YAxis dataKey="name" type="category" stroke="#475569" fontSize={13} tickLine={false} axisLine={false} />
            <Tooltip 
              cursor={{ fill: '#e2e8f0', opacity: 0.4 }}
              contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
            />
            <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

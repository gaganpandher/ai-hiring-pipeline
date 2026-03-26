import React from 'react'
import { AlertOctagon } from 'lucide-react'

interface BiasAlertsProps {
  count: number | undefined
}

export default function BiasAlerts({ count }: BiasAlertsProps) {
  if (!count || count === 0) return null

  return (
    <div className="flex items-center gap-2 px-3 py-1 bg-rose-500/10 border border-rose-500/20 text-rose-500 rounded-lg text-sm font-medium">
      <AlertOctagon size={16} />
      {count} Bias Alert{count !== 1 ? 's' : ''} Active
    </div>
  )
}

import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Briefcase, FileText, BarChart3 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import clsx from 'clsx'

export default function Sidebar() {
  const user = useAuthStore(s => s.user)
  const isRecruiter = user?.role === 'recruiter' || user?.role === 'admin'

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Job Board', path: '/jobs', icon: Briefcase },
    { label: 'Applications', path: '/applications', icon: FileText },
    ...(isRecruiter ? [{ label: 'Analytics', path: '/analytics', icon: BarChart3 }] : [])
  ]

  return (
    <aside className="w-64 glass-panel border-y-0 border-l-0 rounded-none flex flex-col h-full bg-white/80">
      <div className="h-16 flex items-center px-6 border-b border-slate-900/10">
        <div className="flex items-center gap-2">
           <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center text-slate-900 font-bold opacity-90 shadow-lg shadow-indigo-500/20">
             A
           </div>
           <h1 className="text-lg font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
             AI Hiring
           </h1>
        </div>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
              isActive 
                ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-lg shadow-indigo-500/10" 
                : "text-slate-500 hover:text-slate-800 hover:bg-slate-900/5 border border-transparent"
            )}
          >
            <item.icon size={18} className={clsx("transition-transform", 'group-hover:scale-110')} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      
      <div className="p-4 border-t border-slate-900/10">
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
          <h4 className="text-sm font-semibold text-indigo-300 mb-1">Pipeline Engine</h4>
          <p className="text-xs text-indigo-200/60 leading-relaxed">
            AI screening is strictly operating within standard bias parameters.
          </p>
        </div>
      </div>
    </aside>
  )
}

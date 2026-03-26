import { useAuthStore } from '@/store/authStore'
import { LogOut, User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function Topbar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-16 shrink-0 glass-panel border-x-0 border-t-0 rounded-none flex items-center justify-between px-6 md:px-8">
      <div className="text-sm text-slate-500">
        Welcome back, <span className="text-slate-900 font-medium">{user?.full_name || 'User'}</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100/50 border border-slate-200/50">
          <User size={16} className="text-indigo-400" />
          <span className="text-sm font-medium capitalize text-slate-700">
            {user?.role}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-400/10 rounded-xl transition-colors"
          title="Logout"
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  )
}

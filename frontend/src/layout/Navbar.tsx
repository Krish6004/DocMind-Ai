import React, { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Search, MessageSquare, LogOut, User as UserIcon } from 'lucide-react'
import StatusPill from '@/components/common/StatusPill'
import Button from '@/components/common/Button'
import { useAuth } from '@/context/AuthContext'

export interface NavbarProps {
  className?: string
}

const pageTitles: Record<string, { title: string; category: string }> = {
  '/': { title: 'Dashboard', category: 'Overview' },
  '/chat': { title: 'Chat Studio', category: 'Conversational RAG' },
  '/documents': { title: 'Documents', category: 'Knowledge Base' },
  '/analytics': { title: 'Analytics', category: 'Telemetry & Metrics' },
  '/evaluation': { title: 'Evaluation', category: 'RAG Quality & Benchmarks' },
  '/settings': { title: 'Settings', category: 'Configuration' },
}

export const Navbar: React.FC<NavbarProps> = ({ className = '' }) => {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = async () => {
    setMenuOpen(false)
    await logout()
    navigate('/login', { replace: true })
  }

  const initials = (user?.name || 'U')
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  const currentMeta = pageTitles[location.pathname] || {
    title: 'DocMind AI',
    category: 'Enterprise RAG',
  }

  return (
    <header
      className={`h-16 px-6 glass-panel border-b border-white/[0.06] sticky top-0 z-20 flex items-center justify-between backdrop-blur-xl bg-jet-950/60 ${className}`}
    >
      {/* Page Title & Breadcrumb */}
      <div className="flex items-center space-x-2.5">
        <span className="text-xs font-mono text-jet-400 uppercase tracking-wider">
          {currentMeta.category}
        </span>
        <span className="text-jet-600 text-xs">/</span>
        <h1 className="text-sm font-semibold text-white tracking-tight">
          {currentMeta.title}
        </h1>
      </div>

      {/* Global Quick Search Pill */}
      <div className="hidden md:flex items-center w-72 max-w-sm">
        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-jet-400">
            <Search className="w-3.5 h-3.5" />
          </div>
          <input
            type="text"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.target as HTMLInputElement).value.trim()) {
                navigate('/chat', { state: { query: (e.target as HTMLInputElement).value } })
              }
            }}
            placeholder="Search corpus, chunks, prompt..."
            className="w-full pl-8 pr-12 py-1.5 text-xs rounded-xl bg-jet-900/60 border border-white/[0.08] text-jet-200 placeholder-jet-500 focus:outline-none focus:border-cerulean/50 transition-all"
          />
          <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center">
            <kbd className="text-[10px] font-mono text-jet-400 bg-white/5 border border-white/10 px-1 py-0.5 rounded">
              ⌘K
            </kbd>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        <StatusPill showVersion={false} />

        {location.pathname !== '/chat' && (
          <Button
            variant="cerulean"
            size="sm"
            leftIcon={<MessageSquare className="w-3.5 h-3.5" />}
            onClick={() => navigate('/chat')}
            className="shadow-glow-cerulean/30"
          >
            New Chat
          </Button>
        )}

        {/* User Profile Menu & Logout */}
        {user && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center space-x-2 px-2.5 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition-colors"
              title={user.email}
            >
              <span className="w-6 h-6 rounded-lg bg-cerulean/20 border border-cerulean/40 flex items-center justify-center text-[11px] font-mono font-bold text-cerulean-light">
                {initials}
              </span>
              <span className="hidden sm:inline text-xs font-medium text-white max-w-[110px] truncate">
                {user.name}
              </span>
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-jet-950 border border-white/10 shadow-2xl p-2 z-50 space-y-1">
                <div className="px-3 py-2 border-b border-white/[0.06]">
                  <div className="text-xs font-semibold text-white truncate">{user.name}</div>
                  <div className="text-[11px] font-mono text-jet-400 truncate">{user.email}</div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false)
                    navigate('/settings')
                  }}
                  className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs text-jet-300 hover:text-white hover:bg-white/[0.06] transition-colors"
                >
                  <UserIcon className="w-3.5 h-3.5" />
                  <span>Workspace Settings</span>
                </button>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs text-neonrose hover:bg-neonrose/10 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  )
}

export default Navbar

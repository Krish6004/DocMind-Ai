import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Search, MessageSquare } from 'lucide-react'
import StatusPill from '@/components/common/StatusPill'
import Button from '@/components/common/Button'

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
      </div>
    </header>
  )
}

export default Navbar

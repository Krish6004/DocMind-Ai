import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { useHealth } from '@/hooks/useHealth'

export interface StatusPillProps {
  showVersion?: boolean
  className?: string
}

export const StatusPill: React.FC<StatusPillProps> = ({
  showVersion = true,
  className = '',
}) => {
  const { data: health, isLoading, isError, refetch, isFetching } = useHealth()

  if (isLoading) {
    return (
      <div
        className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-jet-800/80 border border-white/10 text-xs text-jet-300 backdrop-blur-md ${className}`}
      >
        <span className="w-2 h-2 rounded-full bg-jet-400 animate-ping" />
        <span className="font-medium">Connecting...</span>
      </div>
    )
  }

  if (isError || !health) {
    return (
      <button
        type="button"
        onClick={() => refetch()}
        title="Backend unreachable. Click to retry connection."
        className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-neonrose/15 border border-neonrose/40 text-xs text-neonrose hover:bg-neonrose/25 transition-all shadow-glow-rose/20 cursor-pointer ${className}`}
      >
        <AlertCircle className="w-3.5 h-3.5" />
        <span className="font-semibold">Backend Offline</span>
        <RefreshCw className={`w-3 h-3 ml-1 ${isFetching ? 'animate-spin' : ''}`} />
      </button>
    )
  }

  const isHealthy = health.status === 'healthy'

  return (
    <div
      className={`inline-flex items-center space-x-2.5 px-3 py-1 rounded-full border backdrop-blur-md transition-all ${
        isHealthy
          ? 'bg-cerulean/15 border-cerulean/35 text-cerulean-light shadow-glow-cerulean/15'
          : 'bg-yellow-500/15 border-yellow-500/35 text-yellow-300'
      } ${className}`}
    >
      <span className="relative flex h-2 w-2">
        <span
          className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
            isHealthy ? 'bg-cerulean' : 'bg-yellow-400'
          }`}
        />
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${
            isHealthy ? 'bg-cerulean-light' : 'bg-yellow-400'
          }`}
        />
      </span>

      <span className="text-xs font-semibold tracking-tight">
        {isHealthy ? 'Backend Ready' : 'Degraded'}
      </span>

      {showVersion && health.version && (
        <span className="text-[10px] text-jet-400 border-l border-white/10 pl-2 font-mono">
          v{health.version}
        </span>
      )}
    </div>
  )
}

export default StatusPill

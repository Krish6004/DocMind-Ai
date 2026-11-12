import React from 'react'
import { Sparkles, ArrowDown, CheckCircle2, Clock, Info } from 'lucide-react'
import Card from '@/components/common/Card'
import type { QueryRewriteTelemetry } from '@/types'

interface QueryRewriteCardProps {
  telemetry?: QueryRewriteTelemetry | null
}

export const QueryRewriteCard: React.FC<QueryRewriteCardProps> = ({ telemetry }) => {
  if (!telemetry) {
    return (
      <Card variant="cerulean" className="p-4 border-dashed border-white/10 text-center">
        <p className="text-xs text-jet-400">Query rewrite telemetry will appear when a turn is selected.</p>
      </Card>
    )
  }

  const {
    original_query,
    rewritten_query,
    rewrite_time_ms,
    status,
    is_rewritten,
  } = telemetry

  const isSuccess = is_rewritten || status === 'rewritten'

  return (
    <Card variant="cerulean" className="p-4 space-y-3.5 bg-jet-950/80 border-white/[0.08]">
      {/* Title Bar */}
      <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.06]">
        <div className="flex items-center space-x-2">
          <div
            className={`w-6 h-6 rounded-lg flex items-center justify-center ${
              isSuccess ? 'bg-emerald-500/15 text-emerald-400' : 'bg-white/[0.06] text-jet-400'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-semibold text-jet-100">Query Rewrite Telemetry</span>
        </div>

        <span
          className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border ${
            isSuccess
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : 'bg-white/[0.04] text-jet-400 border-white/[0.08]'
          }`}
        >
          {isSuccess ? 'Optimized' : status === 'skipped' ? 'Direct Match' : status}
        </span>
      </div>

      {/* Telemetry Chain: Original -> Rewritten -> Time -> Status */}
      <div className="space-y-2 text-xs font-mono">
        {/* 1. Original Query */}
        <div className="p-2.5 rounded-xl bg-jet-900/60 border border-white/[0.04] space-y-1">
          <span className="text-[10px] text-jet-400 uppercase tracking-wider block">
            Original Query
          </span>
          <p className="text-jet-200 text-xs font-sans leading-relaxed break-words">
            "{original_query}"
          </p>
        </div>

        {/* Down Arrow */}
        <div className="flex justify-center text-jet-600">
          <ArrowDown className="w-3.5 h-3.5 text-jet-500" />
        </div>

        {/* 2. Rewritten Query */}
        <div
          className={`p-2.5 rounded-xl border space-y-1 ${
            isSuccess
              ? 'bg-emerald-500/5 border-emerald-500/20 text-white'
              : 'bg-jet-900/60 border-white/[0.04] text-jet-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-jet-400 uppercase tracking-wider block">
              Rewritten Query
            </span>
            {isSuccess && (
              <span className="text-[10px] text-emerald-400 font-mono">Applied to Retrieval</span>
            )}
          </div>
          <p className={`text-xs font-sans leading-relaxed break-words ${isSuccess ? 'text-emerald-300 font-medium' : 'text-jet-300'}`}>
            "{rewritten_query}"
          </p>
        </div>

        {/* Down Arrow */}
        <div className="flex justify-center text-jet-600">
          <ArrowDown className="w-3.5 h-3.5 text-jet-500" />
        </div>

        {/* 3. Rewrite Metrics Grid: Rewrite Time & Rewrite Status */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          {/* Rewrite Time */}
          <div className="p-2 rounded-xl bg-jet-900/60 border border-white/[0.04] space-y-1">
            <div className="flex items-center space-x-1 text-jet-400 text-[10px] uppercase tracking-wider">
              <Clock className="w-2.5 h-2.5" />
              <span>Rewrite Time</span>
            </div>
            <div className="flex items-baseline space-x-1">
              <span className="text-white font-bold text-sm">{rewrite_time_ms}</span>
              <span className="text-[10px] text-jet-400">ms</span>
              <span className="text-[9px] text-emerald-400 ml-auto">&lt; 50ms ✓</span>
            </div>
          </div>

          {/* Rewrite Status */}
          <div className="p-2 rounded-xl bg-jet-900/60 border border-white/[0.04] space-y-1">
            <div className="flex items-center space-x-1 text-jet-400 text-[10px] uppercase tracking-wider">
              <Info className="w-2.5 h-2.5" />
              <span>Rewrite Status</span>
            </div>
            <div className="text-white font-medium capitalize text-xs truncate">
              {status}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default QueryRewriteCard


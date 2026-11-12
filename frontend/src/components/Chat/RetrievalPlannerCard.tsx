import React from 'react'
import Card from '@/components/common/Card'
import type { RetrievalPlannerTelemetry } from '@/types'

interface RetrievalPlannerCardProps {
  planner?: RetrievalPlannerTelemetry | null
}

export const RetrievalPlannerCard: React.FC<RetrievalPlannerCardProps> = ({ planner }) => {
  if (!planner) {
    return (
      <Card variant="cerulean" className="p-3.5 border-dashed border-white/10 text-center">
        <p className="text-xs text-jet-400">Retrieval planner telemetry appears when a turn is selected.</p>
      </Card>
    )
  }

  return (
    <Card variant="cerulean" className="p-3.5 space-y-2.5 bg-jet-950/80 border-white/[0.08]">
      {/* Compact Header */}
      <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
        <span className="text-xs font-semibold text-jet-100 flex items-center gap-1.5">
          <span aria-hidden="true">🧠</span>
          <span>Retrieval Planner</span>
        </span>
        <span className="text-[10px] font-mono text-cerulean-light bg-cerulean/10 border border-cerulean/25 px-2 py-0.5 rounded-full">
          {planner.decision_time_ms.toFixed(2)}ms
        </span>
      </div>

      {/* Compact Metric Grid */}
      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
        <div className="p-2 rounded-lg bg-jet-900/60 border border-white/[0.04]">
          <span className="text-[9px] text-jet-400 uppercase block">Query Type</span>
          <span className="text-white font-semibold capitalize">
            {planner.query_type.replace('_', ' ')}
          </span>
        </div>

        <div className="p-2 rounded-lg bg-jet-900/60 border border-white/[0.04]">
          <span className="text-[9px] text-jet-400 uppercase block">Strategy</span>
          <span className="text-cerulean-light font-medium truncate block" title={planner.strategy_name}>
            {planner.strategy_name}
          </span>
        </div>

        <div className="p-2 rounded-lg bg-jet-900/60 border border-white/[0.04] flex items-center justify-between">
          <span className="text-[10px] text-jet-400">top_k</span>
          <span className="text-white font-bold">{planner.recommended_top_k}</span>
        </div>

        <div className="p-2 rounded-lg bg-jet-900/60 border border-white/[0.04] flex items-center justify-between">
          <span className="text-[10px] text-jet-400">rerank</span>
          <span className="text-white font-bold">{planner.recommended_rerank_count}</span>
        </div>
      </div>

      {/* Decision Time & Reason */}
      <div className="p-2 rounded-lg bg-jet-900/40 border border-white/[0.04] space-y-1 text-[11px]">
        <div className="flex items-center justify-between font-mono text-[10px] text-jet-400">
          <span>Decision Time</span>
          <span className="text-emerald-400 font-medium">{planner.decision_time_ms.toFixed(2)} ms</span>
        </div>
        <p className="text-jet-300 leading-snug text-[11px]">{planner.reason}</p>
      </div>
    </Card>
  )
}

export default RetrievalPlannerCard


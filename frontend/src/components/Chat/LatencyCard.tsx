import React from 'react'
import { motion } from 'framer-motion'
import { Layers, Zap, Sparkles, Timer } from 'lucide-react'
import Card from '@/components/common/Card'
import type { LatencyMetrics } from '@/types'

interface LatencyCardProps {
  metrics?: LatencyMetrics | null
}

export const LatencyCard: React.FC<LatencyCardProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <Card variant="cerulean" className="p-4 border-dashed border-white/10 text-center">
        <p className="text-xs text-jet-400">Select an assistant turn to inspect pipeline latency.</p>
      </Card>
    )
  }

  const {
    retrieval_latency_ms,
    reranking_latency_ms,
    generation_latency_ms,
    total_latency_ms,
    retrieved_chunk_count,
    reranked_chunk_count,
  } = metrics

  const total = Math.max(1, total_latency_ms)
  const retPercent = Math.round((retrieval_latency_ms / total) * 100)
  const rerankPercent = Math.round((reranking_latency_ms / total) * 100)
  const genPercent = Math.round((generation_latency_ms / total) * 100)

  const items = [
    {
      label: 'Retrieval',
      ms: Math.round(retrieval_latency_ms),
      percent: retPercent,
      icon: Layers,
      color: 'text-cerulean-light',
      barColor: 'bg-cerulean',
      sub: `${retrieved_chunk_count} candidates`,
    },
    {
      label: 'Reranking',
      ms: Math.round(reranking_latency_ms),
      percent: rerankPercent,
      icon: Zap,
      color: 'text-neonrose',
      barColor: 'bg-neonrose',
      sub: `${reranked_chunk_count} top chunks`,
    },
    {
      label: 'Generation',
      ms: Math.round(generation_latency_ms),
      percent: genPercent,
      icon: Sparkles,
      color: 'text-cerulean',
      barColor: 'bg-cerulean-light',
      sub: 'Llama-3-70b',
    },
  ]

  return (
    <Card variant="cerulean" className="p-4 space-y-3.5">
      {/* Title Bar */}
      <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.06]">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-lg bg-cerulean/15 flex items-center justify-center text-cerulean-light">
            <Timer className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-semibold text-jet-100">Pipeline Latency</span>
        </div>

        <div className="flex items-center space-x-1 font-mono text-xs">
          <span className="text-jet-400">Total:</span>
          <span className="text-emerald-400 font-bold">{Math.round(total_latency_ms)} ms</span>
        </div>
      </div>

      {/* 3 Metric Rows */}
      <div className="space-y-2.5">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <div
              key={item.label}
              className="p-2.5 rounded-xl bg-jet-950/60 border border-white/[0.04] space-y-1.5"
            >
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-1.5">
                  <Icon className={`w-3.5 h-3.5 ${item.color}`} />
                  <span className="font-medium text-jet-200">{item.label}</span>
                </div>
                <div className="font-mono text-white font-semibold">
                  {item.ms} <span className="text-[10px] text-jet-400 font-normal">ms</span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="h-1.5 w-full rounded-full bg-jet-900 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${item.percent}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                  className={`h-full ${item.barColor}`}
                />
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-jet-400">
                <span>{item.sub}</span>
                <span>{item.percent}% of turn</span>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}

export default LatencyCard

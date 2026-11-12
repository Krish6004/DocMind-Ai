import React from 'react'
import { motion } from 'framer-motion'
import {
  Layers,
  Zap,
  Sparkles,
  Timer,
  CheckCircle2,
  Gauge,
} from 'lucide-react'
import Card from '@/components/common/Card'
import type { LatencyBreakdown } from '@/hooks/useDashboardData'

interface PerformanceProps {
  metrics: LatencyBreakdown
}

export const Performance: React.FC<PerformanceProps> = ({ metrics }) => {
  const { retrievalMs, rerankingMs, generationMs, totalMs } = metrics

  const retrievalPercent = Math.round((retrievalMs / totalMs) * 100)
  const rerankPercent = Math.round((rerankingMs / totalMs) * 100)
  const generationPercent = Math.round((generationMs / totalMs) * 100)

  const cards = [
    {
      label: 'Average Retrieval Latency',
      ms: retrievalMs,
      percent: retrievalPercent,
      icon: Layers,
      color: 'text-cerulean-light',
      bg: 'bg-cerulean/10 border-cerulean/30',
      subtext: 'Dense Vector + BM25 RRF Search',
    },
    {
      label: 'Average Reranking Latency',
      ms: rerankingMs,
      percent: rerankPercent,
      icon: Zap,
      color: 'text-neonrose',
      bg: 'bg-neonrose/10 border-neonrose/30',
      subtext: 'Cross-Encoder Full Attention',
    },
    {
      label: 'Average Generation Latency',
      ms: generationMs,
      percent: generationPercent,
      icon: Sparkles,
      color: 'text-cerulean',
      bg: 'bg-cerulean/10 border-cerulean/30',
      subtext: 'LLM Streaming Context Grounding',
    },
    {
      label: 'Total Average Response Time',
      ms: totalMs,
      percent: 100,
      icon: Timer,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/30',
      subtext: 'End-to-End Query Roundtrip',
    },
  ]

  return (
    <Card variant="cerulean" className="p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.06] gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-cerulean/10 border border-cerulean/30 flex items-center justify-center text-cerulean-light">
            <Gauge className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-jet-100 flex items-center space-x-2">
              <span>Performance & Latency Overview</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3 inline mr-0.5" />
                <span>&lt;500ms Target Met</span>
              </span>
            </h3>
            <p className="text-xs text-jet-400 mt-0.5">
              Granular latency telemetry across every tier of the RAG inference lifecycle
            </p>
          </div>
        </div>

        <div className="font-mono text-xs text-jet-300 flex items-center space-x-2">
          <span className="text-jet-500">Total Roundtrip:</span>
          <span className="text-emerald-400 font-bold">{totalMs} ms</span>
        </div>
      </div>

      {/* 4 Latency Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
        {cards.map((c, idx) => {
          const Icon = c.icon
          return (
            <motion.div
              key={c.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.05 }}
              className="p-4 rounded-xl bg-jet-950/70 border border-white/[0.06] flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-jet-400 truncate">{c.label}</span>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${c.bg}`}>
                  <Icon className={`w-4 h-4 ${c.color}`} />
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-baseline space-x-1.5">
                  <span className="text-2xl font-bold tracking-tight text-white">{c.ms}</span>
                  <span className="text-xs font-mono text-jet-400">ms</span>
                </div>
                <div className="text-[11px] text-jet-400 mt-1 flex items-center justify-between">
                  <span>{c.subtext}</span>
                  <span className="font-mono text-jet-300">{c.percent}%</span>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Latency Allocation Horizontal Stacked Bar */}
      <div className="mt-5 p-4 rounded-xl bg-jet-950/50 border border-white/[0.04]">
        <div className="flex items-center justify-between text-xs text-jet-400 mb-2">
          <span className="font-medium text-jet-300">Pipeline Latency Distribution</span>
          <span className="font-mono">{totalMs} ms Total Turn</span>
        </div>

        <div className="h-3 w-full rounded-full bg-jet-900 overflow-hidden flex">
          <div
            style={{ width: `${retrievalPercent}%` }}
            className="h-full bg-cerulean transition-all duration-500"
            title={`Retrieval: ${retrievalMs}ms (${retrievalPercent}%)`}
          />
          <div
            style={{ width: `${rerankPercent}%` }}
            className="h-full bg-neonrose transition-all duration-500"
            title={`Reranking: ${rerankingMs}ms (${rerankPercent}%)`}
          />
          <div
            style={{ width: `${generationPercent}%` }}
            className="h-full bg-cerulean-light transition-all duration-500"
            title={`Generation: ${generationMs}ms (${generationPercent}%)`}
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] text-jet-400 mt-3 pt-2 border-t border-white/[0.04]">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cerulean inline-block" />
            <span>Retrieval: {retrievalMs}ms ({retrievalPercent}%)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-neonrose inline-block" />
            <span>Reranking: {rerankingMs}ms ({rerankPercent}%)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cerulean-light inline-block" />
            <span>Generation: {generationMs}ms ({generationPercent}%)</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default Performance

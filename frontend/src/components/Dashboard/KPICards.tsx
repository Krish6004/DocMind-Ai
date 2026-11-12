import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  FileText,
  Layers,
  MessageSquare,
  ShieldCheck,
  ArrowUpRight,
} from 'lucide-react'
import Card from '@/components/common/Card'
import type { HealthResponse } from '@/types'

interface KPICardsProps {
  documentsCount: number
  totalChunks: number
  totalQueries: number
  avgConfidence: number
  avgResponseTimeMs?: number
  health?: HealthResponse
  isHealthError?: boolean
}

// Smooth animated counter component
const AnimatedNumber: React.FC<{
  value: number
  decimals?: number
  suffix?: string
}> = ({ value, decimals = 0, suffix = '' }) => {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    let startTimestamp: number | null = null
    const startValue = 0
    const endValue = value
    const duration = 1000

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp
      const progress = Math.min((timestamp - startTimestamp) / duration, 1)
      const easeOut = 1 - Math.pow(1 - progress, 3)
      const current = startValue + (endValue - startValue) * easeOut
      setDisplayValue(current)

      if (progress < 1) {
        window.requestAnimationFrame(step)
      }
    }

    const animId = window.requestAnimationFrame(step)
    return () => window.cancelAnimationFrame(animId)
  }, [value])

  const formatted = decimals > 0
    ? displayValue.toFixed(decimals)
    : Math.round(displayValue).toLocaleString()

  return (
    <span>
      {formatted}
      {suffix}
    </span>
  )
}

export const KPICards: React.FC<KPICardsProps> = ({
  documentsCount,
  totalChunks,
  totalQueries,
  avgConfidence,
}) => {
  // Four KPI cards only as per design specifications
  const kpis = [
    {
      id: 'docs',
      label: 'Indexed Documents',
      value: documentsCount,
      suffix: '',
      decimals: 0,
      subtext: 'PDF, Word, Markdown, Text',
      icon: FileText,
    },
    {
      id: 'chunks',
      label: 'Total Chunks',
      value: totalChunks,
      suffix: '',
      decimals: 0,
      subtext: 'Dense + BM25 Sparse',
      icon: Layers,
    },
    {
      id: 'queries',
      label: 'Queries Handled',
      value: totalQueries,
      suffix: '',
      decimals: 0,
      subtext: 'Reciprocal Rank Fusion',
      icon: MessageSquare,
    },
    {
      id: 'confidence',
      label: 'Average Confidence',
      value: avgConfidence,
      suffix: '%',
      decimals: 1,
      subtext: 'Calibrated High Tier',
      icon: ShieldCheck,
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon

        return (
          <motion.div
            key={kpi.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: idx * 0.04 }}
          >
            <Card
              variant="default"
              className="p-5 h-full relative group hover:border-white/15 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-jet-400">
                  {kpi.label}
                </span>
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-white/[0.04] border border-white/[0.08] text-cerulean-light group-hover:scale-105 transition-transform">
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              <div className="mt-4">
                <div className="text-3xl font-bold tracking-tight text-white font-mono">
                  <AnimatedNumber
                    value={kpi.value}
                    decimals={kpi.decimals}
                    suffix={kpi.suffix}
                  />
                </div>

                <div className="text-[11px] text-jet-400 mt-1.5 flex items-center justify-between">
                  <span>{kpi.subtext}</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-jet-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </Card>
          </motion.div>
        )
      })}
    </div>
  )
}

export default KPICards

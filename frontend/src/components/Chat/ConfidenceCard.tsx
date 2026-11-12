import React from 'react'
import { motion } from 'framer-motion'
import { ShieldCheck, AlertTriangle, AlertCircle } from 'lucide-react'
import Card from '@/components/common/Card'
import type { ConfidenceDetails } from '@/types'

interface ConfidenceCardProps {
  confidence?: ConfidenceDetails | null
}

export const ConfidenceCard: React.FC<ConfidenceCardProps> = ({ confidence }) => {
  if (!confidence) {
    return (
      <Card variant="cerulean" className="p-4 border-dashed border-white/10 text-center">
        <p className="text-xs text-jet-400">Select an assistant turn to view calibrated confidence.</p>
      </Card>
    )
  }

  const { percentage, level, explanation } = confidence

  const isHigh = level === 'High' || percentage >= 85
  const isMedium = level === 'Medium' || (percentage >= 70 && percentage < 85)

  const tierBadgeBg = isHigh
    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
    : isMedium
    ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
    : 'bg-rose-500/15 text-rose-400 border-rose-500/30'

  const Icon = isHigh ? ShieldCheck : isMedium ? AlertTriangle : AlertCircle

  return (
    <Card variant="cerulean" className="p-4 space-y-3.5">
      {/* Title Bar */}
      <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.06]">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-lg bg-cerulean/15 flex items-center justify-center text-cerulean-light">
            <Icon className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-semibold text-jet-100">Answer Confidence</span>
        </div>

        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${tierBadgeBg}`}>
          {level} Tier
        </span>
      </div>

      {/* Large Score Metric */}
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline space-x-1.5">
          <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
            {percentage.toFixed(1)}%
          </span>
          <span className="text-xs text-jet-400">calibrated</span>
        </div>

        <div className="h-2 w-24 rounded-full bg-jet-900 overflow-hidden border border-white/5">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className={`h-full ${isHigh ? 'bg-emerald-400' : isMedium ? 'bg-amber-400' : 'bg-rose-500'}`}
          />
        </div>
      </div>

      {/* Explanation */}
      <div className="p-2.5 rounded-xl bg-jet-950/70 border border-white/[0.04] text-[11px] text-jet-300 leading-relaxed">
        {explanation ||
          'Calculated from reciprocal rank fusion and cross-encoder sequence attention alignment.'}
      </div>

      {/* Mathematical Formula Footnote */}
      <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[10px] font-mono text-jet-400">
        <span className="text-jet-500">Formula:</span>
        <span className="text-cerulean-light truncate">σ(CrossEncoder) × (1 - RRF_penalty)</span>
      </div>
    </Card>
  )
}

export default ConfidenceCard

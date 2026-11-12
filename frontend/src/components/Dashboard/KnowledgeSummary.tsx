import React from 'react'
import { motion } from 'framer-motion'
import {
  FileText,
  FileCode,
  HardDrive,
  Calendar,
  Layers,
  Clock,
  Files,
} from 'lucide-react'
import Card from '@/components/common/Card'
import Badge from '@/components/common/Badge'

interface KnowledgeSummaryProps {
  summary: {
    totalDocs: number
    totalChunks: number
    totalPdf: number
    totalDocx: number
    totalTxt: number
    totalMd: number
    largestDoc: { name: string; size: string }
    newestDoc: { name: string; date: string }
    oldestDoc: { name: string; date: string }
    avgChunksPerDoc: number
    isMock?: boolean
  }
}

export const KnowledgeSummary: React.FC<KnowledgeSummaryProps> = ({ summary }) => {
  const formats = [
    {
      format: 'PDF Documents',
      count: summary.totalPdf,
      icon: FileText,
      color: 'text-cerulean-light',
      bg: 'bg-cerulean/10 border-cerulean/30',
      tag: 'Adobe PDF',
    },
    {
      format: 'DOCX Word Files',
      count: summary.totalDocx,
      icon: Files,
      color: 'text-cerulean',
      bg: 'bg-cerulean/10 border-cerulean/30',
      tag: 'MS Word',
    },
    {
      format: 'Plain Text Files',
      count: summary.totalTxt,
      icon: FileText,
      color: 'text-neonrose',
      bg: 'bg-neonrose/10 border-neonrose/30',
      tag: 'Raw Text',
    },
    {
      format: 'Markdown Files',
      count: summary.totalMd,
      icon: FileCode,
      color: 'text-jet-200',
      bg: 'bg-white/5 border-white/10',
      tag: 'CommonMark',
    },
  ]

  const records = [
    {
      label: 'Largest Document',
      value: summary.largestDoc.name,
      meta: summary.largestDoc.size,
      icon: HardDrive,
      color: 'text-cerulean-light',
    },
    {
      label: 'Newest Document',
      value: summary.newestDoc.name,
      meta: summary.newestDoc.date,
      icon: Clock,
      color: 'text-emerald-400',
    },
    {
      label: 'Oldest Document',
      value: summary.oldestDoc.name,
      meta: summary.oldestDoc.date,
      icon: Calendar,
      color: 'text-amber-400',
    },
    {
      label: 'Average Chunks / Doc',
      value: `${summary.avgChunksPerDoc} chunks`,
      meta: `Across ${summary.totalDocs} total docs`,
      icon: Layers,
      color: 'text-neonrose',
    },
  ]

  return (
    <Card variant="cerulean" className="p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.06] gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-cerulean/10 border border-cerulean/30 flex items-center justify-center text-cerulean-light">
            <Files className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-jet-100 flex items-center space-x-2">
              <span>Knowledge Base Summary</span>
              {summary.isMock && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-jet-800 text-jet-400">
                  Sample Data
                </span>
              )}
            </h3>
            <p className="text-xs text-jet-400 mt-0.5">
              Corpus distribution, file breakdown, and chunking density statistics
            </p>
          </div>
        </div>

        <Badge variant="cerulean" size="sm">
          {summary.totalDocs} Total Corpus Documents
        </Badge>
      </div>

      {/* 4 Format Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 mt-5">
        {formats.map((fmt, idx) => {
          const Icon = fmt.icon
          return (
            <motion.div
              key={fmt.format}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25, delay: idx * 0.05 }}
              className="p-3.5 rounded-xl bg-jet-950/70 border border-white/[0.06] flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-jet-400 truncate">{fmt.format}</span>
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center border ${fmt.bg}`}>
                  <Icon className={`w-3.5 h-3.5 ${fmt.color}`} />
                </div>
              </div>

              <div className="mt-3">
                <span className="text-2xl font-bold text-white">{fmt.count}</span>
                <span className="text-[10px] font-mono text-jet-400 block mt-0.5">{fmt.tag}</span>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* 4 Metadata Record Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mt-4">
        {records.map((rec) => {
          const Icon = rec.icon
          return (
            <div
              key={rec.label}
              className="p-3.5 rounded-xl bg-jet-950/50 border border-white/[0.04] flex items-start space-x-3"
            >
              <div className="w-8 h-8 rounded-lg bg-jet-900 border border-white/10 flex items-center justify-center shrink-0 mt-0.5">
                <Icon className={`w-4 h-4 ${rec.color}`} />
              </div>
              <div className="min-w-0 flex-1">
                <span className="text-[11px] text-jet-400 block font-medium">{rec.label}</span>
                <p className="text-xs font-semibold text-jet-100 truncate mt-0.5" title={rec.value}>
                  {rec.value}
                </p>
                <span className="text-[10px] font-mono text-jet-400 block mt-0.5">{rec.meta}</span>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}

export default KnowledgeSummary

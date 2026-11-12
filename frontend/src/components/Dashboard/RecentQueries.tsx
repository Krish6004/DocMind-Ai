import React from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  MessageSquare,
  ArrowUpRight,
  ShieldCheck,
  FileText,
  Clock,
  Sparkles,
} from 'lucide-react'
import Card from '@/components/common/Card'
import Badge from '@/components/common/Badge'
import Button from '@/components/common/Button'
import type { RecentQueryItem } from '@/hooks/useDashboardData'

interface RecentQueriesProps {
  queries: RecentQueryItem[]
}

export const RecentQueries: React.FC<RecentQueriesProps> = ({ queries }) => {
  const navigate = useNavigate()

  const handleQueryClick = (queryText: string) => {
    navigate('/chat', { state: { query: queryText } })
  }

  return (
    <Card variant="cerulean" className="p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.06] gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-cerulean/10 border border-cerulean/30 flex items-center justify-center text-cerulean-light">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-jet-100 flex items-center space-x-2">
              <span>Recent Inquiries & Grounded Answers</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cerulean/15 text-cerulean-light border border-cerulean/30">
                Interactive
              </span>
            </h3>
            <p className="text-xs text-jet-400 mt-0.5">
              Click any question to open conversational thread with cited context
            </p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          rightIcon={<ArrowUpRight className="w-3.5 h-3.5" />}
          onClick={() => navigate('/chat')}
        >
          Open Chat Studio
        </Button>
      </div>

      {/* Query Cards */}
      <div className="space-y-3 mt-5">
        {queries.map((q, idx) => {
          const confidencePercent = Math.round(q.confidence * 100)
          const isHigh = q.confidenceLevel === 'High'

          return (
            <motion.div
              key={q.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: idx * 0.04 }}
              onClick={() => handleQueryClick(q.query)}
              className="p-4 rounded-xl bg-jet-950/70 border border-white/[0.05] hover:border-cerulean/40 hover:bg-jet-900/60 transition-all cursor-pointer group flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-3.5 h-3.5 text-cerulean-light shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <p className="text-xs sm:text-sm font-medium text-jet-100 group-hover:text-cerulean-light transition-colors line-clamp-1">
                    {q.query}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-[11px] text-jet-400">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-jet-500" />
                    <span>{q.timeAgo}</span>
                  </div>

                  <span>•</span>

                  <div className="flex items-center space-x-1 text-jet-300">
                    <FileText className="w-3 h-3 text-cerulean-light" />
                    <span className="truncate max-w-[200px]" title={q.document}>
                      {q.document}
                    </span>
                  </div>

                  <span>•</span>

                  <span>{q.sourcesCount} sources cited</span>

                  <span>•</span>

                  <span className="font-mono text-jet-300">{q.latencyMs} ms</span>
                </div>
              </div>

              {/* Confidence Pill & Action */}
              <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                <Badge
                  variant={isHigh ? 'cerulean' : 'warning'}
                  size="sm"
                  className="font-mono text-[11px]"
                >
                  <ShieldCheck className="w-3 h-3 mr-1 inline" />
                  {confidencePercent}% {q.confidenceLevel}
                </Badge>

                <div className="w-8 h-8 rounded-lg bg-jet-900 border border-white/5 flex items-center justify-center text-jet-400 group-hover:text-cerulean-light group-hover:border-cerulean/30 transition-colors">
                  <ArrowUpRight className="w-4 h-4" />
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </Card>
  )
}

export default RecentQueries


import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  UploadCloud,
  Layers,
  MessageSquare,
  Trash2,
  Clock,
} from 'lucide-react'
import Card from '@/components/common/Card'
import type { ActivityItem } from '@/hooks/useDashboardData'

interface RecentActivityProps {
  activities: ActivityItem[]
}

export const RecentActivity: React.FC<RecentActivityProps> = ({ activities }) => {
  const [filter, setFilter] = useState<'all' | 'upload' | 'chat' | 'indexing' | 'delete'>('all')

  const filtered = activities.filter((act) => {
    if (filter === 'all') return true
    return act.type === filter
  })

  const getEventIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'upload':
        return {
          icon: UploadCloud,
          color: 'text-cerulean-light',
          bg: 'bg-cerulean/10 border-cerulean/20',
        }
      case 'indexing':
        return {
          icon: Layers,
          color: 'text-cerulean-light',
          bg: 'bg-cerulean/10 border-cerulean/20',
        }
      case 'chat':
        return {
          icon: MessageSquare,
          color: 'text-white',
          bg: 'bg-white/10 border-white/15',
        }
      case 'delete':
        return {
          icon: Trash2,
          color: 'text-neonrose',
          bg: 'bg-neonrose/10 border-neonrose/20',
        }
    }
  }

  return (
    <Card variant="default" className="p-6 border border-white/[0.08]">
      {/* Header and Filter Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.06] gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center text-jet-300">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Live Operations Activity</h3>
            <p className="text-xs text-jet-400 mt-0.5">
              Chronological log of document ingestion, vector indexing, and query turns
            </p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center space-x-1 overflow-x-auto pb-1 sm:pb-0">
          {(
            [
              { id: 'all', label: 'All' },
              { id: 'upload', label: 'Uploads' },
              { id: 'indexing', label: 'Indexing' },
              { id: 'chat', label: 'Queries' },
              { id: 'delete', label: 'Purged' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                filter === tab.id
                  ? 'bg-white/10 text-white border border-white/15'
                  : 'text-jet-400 hover:text-jet-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Activity Timeline List */}
      <div className="mt-5 space-y-3">
        {filtered.length === 0 ? (
          <div className="py-8 text-center text-xs text-jet-400">
            No activity recorded in this category.
          </div>
        ) : (
          filtered.slice(0, 6).map((item, idx) => {
            const { icon: Icon, color, bg } = getEventIcon(item.type)

            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: idx * 0.03 }}
                className="p-3.5 rounded-xl bg-jet-950/60 border border-white/[0.04] hover:border-white/10 transition-colors flex items-center justify-between gap-3 group"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center border shrink-0 ${bg}`}
                  >
                    <Icon className={`w-4 h-4 ${color}`} />
                  </div>

                  <div className="min-w-0">
                    <p className="text-xs font-medium text-jet-100 truncate group-hover:text-white transition-colors">
                      {item.title}
                    </p>
                    <p className="text-[11px] text-jet-400 truncate mt-0.5">
                      {item.description}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  {item.badgeText && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/5 text-jet-300">
                      {item.badgeText}
                    </span>
                  )}
                  <span className="text-[10px] font-mono text-jet-400">
                    {item.relativeTime}
                  </span>
                </div>
              </motion.div>
            )
          })
        )}
      </div>
    </Card>
  )
}

export default RecentActivity

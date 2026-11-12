import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown,
  ChevronUp,
  Award,
  Copy,
  Check,
  BookOpen,
} from 'lucide-react'
import Card from '@/components/common/Card'
import type { SourceChunk } from '@/types'

interface SourceDrawerProps {
  sources?: SourceChunk[] | null
  highlightedSourceNum?: number | null
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({
  sources,
  highlightedSourceNum,
}) => {
  const [expandedId, setExpandedId] = useState<number | null>(sources?.[0]?.source_num ?? 1)
  const [copiedId, setCopiedId] = useState<number | null>(null)

  if (!sources || sources.length === 0) {
    return (
      <Card variant="cerulean" className="p-4 border-dashed border-white/10 text-center">
        <p className="text-xs text-jet-400">No attributed source chunks for this response.</p>
      </Card>
    )
  }

  const handleCopyText = (sourceNum: number, text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(sourceNum)
    setTimeout(() => setCopiedId(null), 1800)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between px-1">
        <span className="text-xs font-semibold text-jet-100 flex items-center space-x-1.5">
          <BookOpen className="w-3.5 h-3.5 text-cerulean-light" />
          <span>Attributed Citations ({sources.length})</span>
        </span>
        <span className="text-[10px] font-mono text-jet-400">RRF + ms-marco</span>
      </div>

      <div className="space-y-2.5">
        {sources.map((src, index) => {
          const isPrimary = index === 0
          const isExpanded = expandedId === src.source_num
          const isHighlighted = highlightedSourceNum === src.source_num
          const page = src.metadata?.page_number ?? src.metadata?.page ?? (index + 1)
          const similarityPercent = Math.round(src.score * 100)

          return (
            <div
              key={src.source_num}
              className={`rounded-xl border transition-all duration-200 overflow-hidden ${
                isHighlighted
                  ? 'bg-cerulean/15 border-cerulean shadow-glow-cerulean/30 ring-1 ring-cerulean/50'
                  : 'bg-jet-950/70 border-white/[0.06] hover:border-white/15'
              }`}
            >
              {/* Collapsible Header */}
              <button
                type="button"
                onClick={() => setExpandedId(isExpanded ? null : src.source_num)}
                className="w-full p-3 flex items-center justify-between text-left gap-2"
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <div
                    className={`w-6 h-6 rounded-md flex items-center justify-center font-mono text-xs font-bold shrink-0 ${
                      isPrimary
                        ? 'bg-cerulean text-white shadow-glow-cerulean'
                        : 'bg-jet-900 text-jet-300 border border-white/10'
                    }`}
                  >
                    [{src.source_num}]
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <p className="text-xs font-medium text-jet-100 truncate" title={src.filename}>
                        {src.filename}
                      </p>
                      {isPrimary && (
                        <span className="inline-flex items-center px-1.5 py-0.2 rounded-full text-[9px] font-semibold bg-cerulean/20 text-cerulean-light border border-cerulean/40">
                          <Award className="w-2.5 h-2.5 mr-0.5 inline" /> Primary
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 text-[10px] font-mono text-jet-400 mt-0.5">
                      <span>Chunk #{src.chunk_index}</span>
                      <span>•</span>
                      <span>Page {page}</span>
                      <span>•</span>
                      <span className="text-emerald-400 font-semibold">{similarityPercent}% Match</span>
                    </div>
                  </div>
                </div>

                <div className="text-jet-400 hover:text-white shrink-0">
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </button>

              {/* Expanded Excerpt Body */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="border-t border-white/[0.04] bg-jet-900/40 p-3 space-y-2.5"
                  >
                    {/* Score Breakdown Pills */}
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                      <span className="px-2 py-0.5 rounded bg-jet-950 border border-white/5 text-jet-300">
                        Score: {src.score.toFixed(4)}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-jet-950 border border-white/5 text-jet-300">
                        Reranker: ms-marco
                      </span>
                      <span className="px-2 py-0.5 rounded bg-jet-950 border border-white/5 text-jet-300">
                        Density: {src.text ? src.text.length : 0} chars
                      </span>
                    </div>

                    {/* Extracted Text Content with Evidence Quote styling */}
                    <div className="p-2.5 rounded-lg bg-jet-950/80 border border-white/[0.04] text-[11px] leading-relaxed text-jet-200 font-sans max-h-48 overflow-y-auto">
                      <p className="italic text-jet-300">
                        "{src.text || 'Grounded passage text extracted from vector chunk.'}"
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-end space-x-2 pt-1">
                      <button
                        type="button"
                        onClick={() => handleCopyText(src.source_num, src.text || '')}
                        className="flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-medium text-jet-300 hover:text-white bg-white/5 hover:bg-white/10 transition-colors"
                      >
                        {copiedId === src.source_num ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-400" />
                            <span className="text-emerald-400">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy Excerpt</span>
                          </>
                        )}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default SourceDrawer

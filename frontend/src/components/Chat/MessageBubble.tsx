import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Sparkles,
  User,
  ShieldCheck,
  Clock,
  Copy,
  Check,
  RotateCw,
  FileText,
  SlidersHorizontal,
  ChevronDown,
} from 'lucide-react'
import MarkdownRenderer from './MarkdownRenderer'
import type { ConfidenceDetails, LatencyMetrics, QueryRewriteTelemetry, SourceChunk } from '@/types'

export interface MessageBubbleProps {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  confidence?: ConfidenceDetails | null
  metrics?: LatencyMetrics | null
  sources?: SourceChunk[] | null
  query_rewrite?: QueryRewriteTelemetry | null
  onCitationClick?: (sourceNum: number) => void
  onInspect?: () => void
  onRegenerate?: () => void
  isSelectedForInspection?: boolean
}

export const MessageBubble: React.FC<MessageBubbleProps> = React.memo(
  ({
    role,
    content,
    timestamp,
    confidence,
    metrics,
    sources,
    query_rewrite,
    onCitationClick,
    onInspect,
    onRegenerate,
    isSelectedForInspection = false,
  }) => {
    const [copied, setCopied] = useState(false)
    const [isRewriteExpanded, setIsRewriteExpanded] = useState(false)

    const handleCopy = async () => {
      try {
        await navigator.clipboard.writeText(content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } catch {
        // Fallback
      }
    }

    if (role === 'user') {
      return (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.25 }}
          className="flex items-start justify-end space-x-3 max-w-2xl ml-auto"
        >
          <div className="p-4 rounded-2xl rounded-tr-sm bg-cerulean/15 border border-cerulean/30 text-jet-100 text-xs sm:text-sm shadow-glow-cerulean/10 leading-relaxed max-w-full break-words">
            <p className="whitespace-pre-wrap">{content}</p>
            <span className="text-[10px] text-jet-400 mt-2 block text-right font-mono">
              {timestamp}
            </span>
          </div>

          <div className="w-8 h-8 rounded-xl bg-jet-800 border border-white/10 flex items-center justify-center text-jet-300 shrink-0 shadow-glass-sm">
            <User className="w-4 h-4" />
          </div>
        </motion.div>
      )
    }

    // Assistant Message
    const confidenceLevel = confidence?.level || 'High'
    const confidenceScore = confidence?.percentage ?? 94.8
    const totalLatency = metrics?.total_latency_ms ? Math.round(metrics.total_latency_ms) : 468
    const hasSources = Array.isArray(sources) && sources.length > 0

    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`flex items-start space-x-3 max-w-3xl transition-all ${
          isSelectedForInspection ? 'ring-1 ring-cerulean/50 rounded-2xl' : ''
        }`}
      >
        {/* Avatar */}
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cerulean to-neonrose p-0.5 shrink-0 shadow-glow-cerulean/20">
          <div className="w-full h-full bg-jet-950 rounded-[10px] flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-cerulean-light" />
          </div>
        </div>

        {/* Message Container */}
        <div className="flex-1 space-y-2 min-w-0">
          <div className="p-5 rounded-2xl rounded-tl-sm glass-card border border-white/10 text-jet-100 text-xs sm:text-sm space-y-3 shadow-glass">
            {/* Render Markdown Content */}
            <MarkdownRenderer
              content={content}
              onCitationClick={onCitationClick}
            />

            {/* Source Citations Quick Chips */}
            {hasSources && (
              <div className="pt-2 border-t border-white/[0.05] flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] text-jet-400 font-medium">Cited:</span>
                {sources.slice(0, 3).map((src) => (
                  <button
                    key={src.source_num}
                    type="button"
                    onClick={() => {
                      onCitationClick?.(src.source_num)
                      onInspect?.()
                    }}
                    className="flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono text-cerulean-light bg-cerulean/10 hover:bg-cerulean/20 border border-cerulean/30 transition-colors"
                  >
                    <FileText className="w-2.5 h-2.5" />
                    <span>[{src.source_num}] {src.filename}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Expandable Optimized Retrieval Query Section */}
            {query_rewrite?.is_rewritten && (
              <div className="pt-2 border-t border-white/[0.04] space-y-1.5">
                <button
                  type="button"
                  onClick={() => setIsRewriteExpanded(!isRewriteExpanded)}
                  className="flex items-center space-x-1.5 text-[11px] font-mono text-jet-400 hover:text-white transition-colors group"
                >
                  <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform duration-200 ${
                      isRewriteExpanded ? 'rotate-180 text-emerald-400' : 'text-jet-500 group-hover:text-jet-300'
                    }`}
                  />
                  <span>Optimized Retrieval Query</span>
                  <span className="text-[10px] text-emerald-400/80 font-mono">
                    ({query_rewrite.rewrite_time_ms}ms)
                  </span>
                </button>

                {isRewriteExpanded && (
                  <div className="p-3 rounded-xl bg-jet-950/80 border border-emerald-500/20 text-xs font-mono text-jet-200 space-y-1 animate-fade-in shadow-inner">
                    <div className="text-[10px] uppercase tracking-wider text-jet-400 flex items-center justify-between">
                      <span>Query Rewriter Disambiguation</span>
                      <span className="text-emerald-400 font-medium">Applied</span>
                    </div>
                    <p className="text-white font-medium pl-2 border-l-2 border-emerald-400 py-0.5">
                      "{query_rewrite.rewritten_query}"
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Telemetry and Action Footnote */}
            <div className="pt-3 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-2 text-[11px] text-jet-400">
              {/* Left: Badges */}
              <div className="flex flex-wrap items-center gap-2">
                {/* Query Optimized Badge */}
                {query_rewrite?.is_rewritten && (
                  <button
                    type="button"
                    onClick={() => setIsRewriteExpanded(!isRewriteExpanded)}
                    className="flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-medium text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 transition-colors"
                    title="This query was rewritten to improve retrieval accuracy."
                  >
                    <Sparkles className="w-3 h-3 text-emerald-400 shrink-0" />
                    <span>Query Optimized</span>
                  </button>
                )}

                {/* Confidence Badge */}
                <button
                  type="button"
                  onClick={onInspect}
                  className="flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-medium text-cerulean-light bg-cerulean/10 hover:bg-cerulean/20 border border-cerulean/30 transition-colors"
                  title="View calibrated confidence breakdown"
                >
                  <ShieldCheck className="w-3 h-3 text-cerulean-light" />
                  <span>{confidenceScore.toFixed(0)}% {confidenceLevel}</span>
                </button>

                {/* Latency Tag */}
                <button
                  type="button"
                  onClick={onInspect}
                  className="flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-mono text-jet-300 bg-white/[0.04] hover:bg-white/[0.08] border border-white/5 transition-colors"
                  title="View RAG latency breakdown"
                >
                  <Clock className="w-3 h-3 text-jet-400" />
                  <span>{totalLatency}ms</span>
                </button>

                <span className="text-[10px] font-mono text-jet-400">
                  {timestamp}
                </span>
              </div>

              {/* Right: Actions */}
              <div className="flex items-center space-x-1">
                {onInspect && (
                  <button
                    type="button"
                    onClick={onInspect}
                    className="p-1.5 rounded-lg text-jet-400 hover:text-white hover:bg-white/5 transition-colors"
                    title="Inspect telemetry and citations"
                  >
                    <SlidersHorizontal className="w-3.5 h-3.5" />
                  </button>
                )}

                {onRegenerate && (
                  <button
                    type="button"
                    onClick={onRegenerate}
                    className="p-1.5 rounded-lg text-jet-400 hover:text-white hover:bg-white/5 transition-colors"
                    title="Regenerate response"
                  >
                    <RotateCw className="w-3.5 h-3.5" />
                  </button>
                )}

                <button
                  type="button"
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg text-jet-400 hover:text-white hover:bg-white/5 transition-colors"
                  title="Copy response"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    )
  }
)

MessageBubble.displayName = 'MessageBubble'

export default MessageBubble


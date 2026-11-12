import React, { useRef, useEffect, useState } from 'react'
import { ArrowDown } from 'lucide-react'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import EmptyState from './EmptyState'
import type {
  ConfidenceDetails,
  LatencyMetrics,
  QueryRewriteTelemetry,
  RetrievalPlannerTelemetry,
  SourceChunk,
} from '@/types'

export interface ChatMessageItem {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  confidence?: ConfidenceDetails | null
  metrics?: LatencyMetrics | null
  sources?: SourceChunk[] | null
  query_rewrite?: QueryRewriteTelemetry | null
  retrieval_planner?: RetrievalPlannerTelemetry | null
}

interface ChatMessagesProps {
  messages: ChatMessageItem[]
  isGenerating?: boolean
  onCitationClick?: (sourceNum: number) => void
  onInspectMessage?: (msg: ChatMessageItem) => void
  onRegenerate?: (query: string) => void
  onStop?: () => void
  onSelectPrompt: (prompt: string) => void
  selectedMessageId?: string | null
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isGenerating = false,
  onCitationClick,
  onInspectMessage,
  onRegenerate,
  onStop,
  onSelectPrompt,
  selectedMessageId,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [showScrollBottom, setShowScrollBottom] = useState(false)

  // Scroll to bottom
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    bottomRef.current?.scrollIntoView({ behavior })
  }

  // Handle auto-scroll on new message or generation
  useEffect(() => {
    if (!showScrollBottom) {
      scrollToBottom('smooth')
    }
  }, [messages.length, isGenerating, showScrollBottom])

  // Track scroll position to toggle scroll-to-bottom button
  const handleScroll = () => {
    const el = containerRef.current
    if (!el) return
    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    setShowScrollBottom(distanceToBottom > 150)
  }

  if (messages.length === 0 && !isGenerating) {
    return (
      <div className="flex-1 overflow-y-auto flex flex-col justify-center">
        <EmptyState onSelectPrompt={onSelectPrompt} />
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto p-4 sm:p-6 relative"
    >
      <div className="max-w-4xl mx-auto w-full space-y-6">
        {messages.map((msg, index) => {
          // If assistant, find the preceding user query for regeneration
          let precedingQuery = ''
          if (msg.role === 'assistant' && index > 0 && messages[index - 1].role === 'user') {
            precedingQuery = messages[index - 1].content
          }

          return (
            <MessageBubble
              key={msg.id}
              id={msg.id}
              role={msg.role}
              content={msg.content}
              timestamp={msg.timestamp}
              confidence={msg.confidence}
              metrics={msg.metrics}
              sources={msg.sources}
              query_rewrite={msg.query_rewrite}
              onCitationClick={onCitationClick}
              onInspect={() => onInspectMessage?.(msg)}
              onRegenerate={precedingQuery ? () => onRegenerate?.(precedingQuery) : undefined}
              isSelectedForInspection={selectedMessageId === msg.id}
            />
          )
        })}

        {/* Typing indicator when model is thinking / retrieving */}
        {isGenerating && <TypingIndicator onStop={onStop} />}

        <div ref={bottomRef} className="h-2" />
      </div>

      {/* Floating Scroll to Bottom Button */}
      {showScrollBottom && (
        <button
          type="button"
          onClick={() => scrollToBottom('smooth')}
          className="sticky bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-jet-900/90 text-cerulean-light border border-cerulean/30 shadow-glass-md hover:bg-jet-800 transition-all text-xs font-medium"
        >
          <ArrowDown className="w-3.5 h-3.5" />
          <span>Scroll to latest</span>
        </button>
      )}
    </div>
  )
}

export default ChatMessages

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookmarkCheck,
  Cpu,
  X,
} from 'lucide-react'
import ConversationSidebar from './ConversationSidebar'
import ChatHeader from './ChatHeader'
import ChatMessages from './ChatMessages'
import PromptInput from './PromptInput'
import SuggestedPrompts from './SuggestedPrompts'
import ConfidenceCard from './ConfidenceCard'
import LatencyCard from './LatencyCard'
import QueryRewriteCard from './QueryRewriteCard'
import RetrievalPlannerCard from './RetrievalPlannerCard'
import SourceDrawer from './SourceDrawer'
import { useChatWorkspace } from '@/hooks/useChatWorkspace'

interface ChatLayoutProps {
  initialQuery?: string
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({ initialQuery }) => {
  const {
    sessions,
    activeSessionId,
    activeSession,
    messages,
    isGenerating,
    promptInputRef,
    drawerOpen,
    sidebarOpen,
    selectedMessageId,
    highlightedSourceNum,
    activeInspectedMessage,
    setDrawerOpen,
    setSidebarOpen,
    setSelectedMessageId,
    setHighlightedSourceNum,
    sendMessage,
    stopGeneration,
    handleNewChat,
    handleSelectSession,
    handleDeleteSession,
    handleRenameSession,
    handleTogglePin,
    handleClearCurrentMessages,
  } = useChatWorkspace()

  const [promptText, setPromptText] = useState(initialQuery || '')
  const lastInitialQueryRef = React.useRef(initialQuery)

  // If initialQuery changes from navigation state
  React.useEffect(() => {
    if (initialQuery && initialQuery !== lastInitialQueryRef.current) {
      lastInitialQueryRef.current = initialQuery
      setPromptText(initialQuery)
      promptInputRef.current?.focus()
    }
  }, [initialQuery, promptInputRef])

  const handleSendPrompt = () => {
    if (!promptText.trim()) return
    const textToSend = promptText
    setPromptText('')
    sendMessage(textToSend)
  }

  const handleSelectSuggestedPrompt = (prompt: string) => {
    setPromptText('')
    sendMessage(prompt)
  }

  return (
    <div className="flex h-[calc(100vh-5.5rem)] gap-4 overflow-hidden relative">
      {/* 1. Left Sidebar: Conversation History */}
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0, width: 0, x: -20 }}
            animate={{ opacity: 1, width: 'auto', x: 0 }}
            exit={{ opacity: 0, width: 0, x: -20 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="hidden md:flex h-full shrink-0"
          >
            <ConversationSidebar
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSelectSession={handleSelectSession}
              onNewChat={handleNewChat}
              onDeleteSession={handleDeleteSession}
              onRenameSession={handleRenameSession}
              onTogglePin={handleTogglePin}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 2. Center Column: Main Chat Studio */}
      <div className="flex-1 flex flex-col glass-panel rounded-3xl border border-white/10 overflow-hidden relative shadow-glass-lg min-w-0">
        {/* Chat Control Toolbar Header */}
        <ChatHeader
          sessionTitle={activeSession?.title || 'DocMind RAG Session'}
          modelName="Llama-3-70b (Groq)"
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          drawerOpen={drawerOpen}
          onToggleDrawer={() => setDrawerOpen(!drawerOpen)}
          onClearChat={handleClearCurrentMessages}
          messagesCount={messages.length}
        />

        {/* Message Thread Area */}
        <ChatMessages
          messages={messages}
          isGenerating={isGenerating}
          onCitationClick={(num) => {
            setHighlightedSourceNum(num)
            if (!drawerOpen) setDrawerOpen(true)
          }}
          onInspectMessage={(msg) => {
            setSelectedMessageId(msg.id)
            if (!drawerOpen) setDrawerOpen(true)
          }}
          onRegenerate={(query) => sendMessage(query)}
          onStop={stopGeneration}
          onSelectPrompt={handleSelectSuggestedPrompt}
          selectedMessageId={selectedMessageId}
        />

        {/* Floating Input Dock Area */}
        <div className="p-3 sm:p-4 border-t border-white/[0.08] bg-jet-950/70 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto w-full space-y-2">
            {/* Suggested Prompts Carousel */}
            {messages.length > 0 && (
              <SuggestedPrompts
                onSelectPrompt={handleSelectSuggestedPrompt}
                disabled={isGenerating}
              />
            )}

            {/* Auto-expanding Prompt Box */}
            <PromptInput
              value={promptText}
              onChange={setPromptText}
              onSend={handleSendPrompt}
              onStop={stopGeneration}
              isGenerating={isGenerating}
              inputRef={promptInputRef}
            />
          </div>
        </div>
      </div>

      {/* 3. Right Sidebar: Inspection & Intelligence Drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            initial={{ opacity: 0, width: 0, x: 20 }}
            animate={{ opacity: 1, width: 340, x: 0 }}
            exit={{ opacity: 0, width: 0, x: 20 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="hidden xl:flex flex-col glass-panel rounded-3xl border border-white/10 overflow-hidden shrink-0 shadow-glass-lg"
          >
            {/* Drawer Header */}
            <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-jet-950/60">
              <div className="flex items-center space-x-2">
                <BookmarkCheck className="w-4 h-4 text-cerulean-light" />
                <h3 className="text-xs font-semibold text-jet-100">RAG Telemetry & Evidence</h3>
              </div>

              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                className="p-1 rounded-lg text-jet-400 hover:text-white hover:bg-white/5 transition-colors"
                title="Close drawer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Body Scroll Container */}
            <div className="p-4 overflow-y-auto space-y-4 flex-1">
              {/* Confidence Card */}
              <ConfidenceCard confidence={activeInspectedMessage?.confidence} />

              {/* Adaptive Retrieval Planner Card */}
              <RetrievalPlannerCard planner={activeInspectedMessage?.retrieval_planner} />

              {/* Query Rewrite Telemetry Card */}
              <QueryRewriteCard telemetry={activeInspectedMessage?.query_rewrite} />

              {/* Latency Card */}
              <LatencyCard metrics={activeInspectedMessage?.metrics} />

              {/* Attributed Source Chunks */}
              <SourceDrawer
                sources={activeInspectedMessage?.sources}
                highlightedSourceNum={highlightedSourceNum}
              />

              {/* System Architecture Specifications */}
              <div className="p-3.5 rounded-xl bg-jet-950/60 border border-white/[0.04] space-y-2 text-[11px] font-mono">
                <div className="flex items-center space-x-1.5 text-jet-300 font-semibold pb-1.5 border-b border-white/[0.04]">
                  <Cpu className="w-3.5 h-3.5 text-cerulean-light" />
                  <span>Pipeline Specifications</span>
                </div>
                <div className="flex justify-between text-jet-400">
                  <span>Inference:</span>
                  <span className="text-jet-200">Llama-3-70b-Versatile</span>
                </div>
                <div className="flex justify-between text-jet-400">
                  <span>Embedding:</span>
                  <span className="text-jet-200">BAAI/bge-small-en (384d)</span>
                </div>
                <div className="flex justify-between text-jet-400">
                  <span>Reranker:</span>
                  <span className="text-jet-200">ms-marco-MiniLM-L-6-v2</span>
                </div>
                <div className="flex justify-between text-jet-400">
                  <span>Fusion:</span>
                  <span className="text-jet-200">RRF (k=60) + BM25</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ChatLayout

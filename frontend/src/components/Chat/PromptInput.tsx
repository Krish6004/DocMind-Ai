import React, { useRef, useEffect } from 'react'
import {
  Send,
  Paperclip,
  Mic,
  X,
  Square,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface PromptInputProps {
  value: string
  onChange: (val: string) => void
  onSend: () => void
  onStop?: () => void
  isGenerating?: boolean
  inputRef?: React.RefObject<HTMLTextAreaElement | null>
}

export const PromptInput: React.FC<PromptInputProps> = ({
  value,
  onChange,
  onSend,
  onStop,
  isGenerating = false,
  inputRef,
}) => {
  const navigate = useNavigate()
  const localRef = useRef<HTMLTextAreaElement>(null)
  const textareaRef = inputRef || localRef

  // Auto-resize textarea height
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      const newHeight = Math.min(el.scrollHeight, 180)
      el.style.height = `${Math.max(52, newHeight)}px`
    }
  }, [value, textareaRef])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim() && !isGenerating) {
        onSend()
      }
    }
  }

  const handleClear = () => {
    onChange('')
    textareaRef.current?.focus()
  }

  return (
    <div className="relative rounded-2xl glass-panel border border-white/10 shadow-glass-lg transition-all focus-within:border-cerulean/50 focus-within:ring-1 focus-within:ring-cerulean/30">
      <div className="flex items-end px-3 py-2.5 gap-2">
        {/* Upload Shortcut Button */}
        <button
          type="button"
          onClick={() => navigate('/documents')}
          className="p-2.5 rounded-xl text-jet-400 hover:text-white hover:bg-white/5 active:scale-95 transition-all shrink-0"
          title="Attach or manage documents"
          aria-label="Upload document"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Auto-expanding Textarea */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about your uploaded documents..."
          className="w-full py-2 bg-transparent text-xs sm:text-sm text-jet-100 placeholder-jet-500 focus:outline-none resize-none leading-relaxed min-h-[44px] max-h-[180px]"
        />

        {/* Clear Button (only shown if value is not empty) */}
        {value.length > 0 && !isGenerating && (
          <button
            type="button"
            onClick={handleClear}
            className="p-2 text-jet-400 hover:text-white hover:bg-white/5 rounded-xl transition-all shrink-0 active:scale-95"
            title="Clear prompt"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Voice Dictation (UI placeholder) */}
        <button
          type="button"
          onClick={() => alert('Voice dictation is scheduled for DocMind Studio v2.1.')}
          className="p-2.5 rounded-xl text-jet-400 hover:text-white hover:bg-white/5 active:scale-95 transition-all shrink-0 hidden sm:flex"
          title="Voice dictation (Coming soon)"
          aria-label="Voice input"
        >
          <Mic className="w-4 h-4" />
        </button>

        {/* Send / Stop Generation Button */}
        {isGenerating ? (
          <button
            type="button"
            onClick={onStop}
            className="p-2.5 rounded-xl bg-neonrose text-white hover:bg-neonrose-light active:scale-95 transition-all shadow-glow-rose shrink-0"
            title="Stop generation"
            aria-label="Stop generation"
          >
            <Square className="w-4 h-4 fill-current" />
          </button>
        ) : (
          <button
            type="button"
            disabled={!value.trim()}
            onClick={onSend}
            className={`p-2.5 rounded-xl transition-all shrink-0 ${
              value.trim()
                ? 'bg-cerulean text-white hover:bg-cerulean-light shadow-glow-cerulean active:scale-95 cursor-pointer'
                : 'bg-white/5 text-jet-500 cursor-not-allowed'
            }`}
            title="Send query"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Footer Hints Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 border-t border-white/[0.04] text-[10px] text-jet-400 font-mono">
        <div className="flex items-center space-x-2">
          <span>Enter ↵ to send</span>
          <span>•</span>
          <span>Shift+Enter for newline</span>
        </div>
        <div className="hidden sm:flex items-center space-x-1">
          <kbd className="px-1.5 py-0.5 rounded bg-jet-900 border border-white/10 text-jet-300">
            Ctrl+K
          </kbd>
          <span>focus</span>
        </div>
      </div>
    </div>
  )
}

export default PromptInput

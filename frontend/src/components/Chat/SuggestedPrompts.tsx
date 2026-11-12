import React from 'react'
import { Sparkles, ArrowRight } from 'lucide-react'

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void
  disabled?: boolean
}

const DEFAULT_SUGGESTED_PROMPTS = [
  'Summarize this document',
  'What are the key findings?',
  'Explain this report',
  'Give me important points',
  'Generate interview questions',
  'Extract action items',
]

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({
  onSelectPrompt,
  disabled = false,
}) => {
  return (
    <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none py-1">
      <div className="flex items-center space-x-1.5 text-xs text-jet-400 font-medium shrink-0 pl-1">
        <Sparkles className="w-3.5 h-3.5 text-cerulean-light" />
        <span className="hidden sm:inline">Suggested:</span>
      </div>

      <div className="flex items-center space-x-2 shrink-0">
        {DEFAULT_SUGGESTED_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={disabled}
            onClick={() => onSelectPrompt(prompt)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-jet-300 bg-jet-950/70 border border-white/10 hover:border-cerulean/40 hover:text-white hover:bg-cerulean/10 active:scale-95 transition-all shadow-glass-sm shrink-0 disabled:opacity-50 disabled:pointer-events-none group"
          >
            <span>{prompt}</span>
            <ArrowRight className="w-3 h-3 text-jet-500 group-hover:text-cerulean-light group-hover:translate-x-0.5 transition-all" />
          </button>
        ))}
      </div>
    </div>
  )
}

export default SuggestedPrompts

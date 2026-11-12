import React, { useState } from 'react'
import { Check, Copy, Terminal } from 'lucide-react'

interface CodeBlockProps {
  language?: string
  value: string
}

export const CodeBlock: React.FC<CodeBlockProps> = React.memo(({ language = 'text', value }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback
    }
  }

  const cleanLang = (language || 'text').replace(/^language-/, '').toLowerCase()

  return (
    <div className="relative my-4 rounded-xl border border-white/10 bg-jet-950 overflow-hidden shadow-glass-sm group">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/[0.08] bg-jet-900/80 text-xs font-mono">
        <div className="flex items-center space-x-2 text-jet-400">
          <Terminal className="w-3.5 h-3.5 text-cerulean-light" />
          <span className="uppercase text-[11px] font-semibold tracking-wider text-jet-300">
            {cleanLang}
          </span>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] font-sans transition-all text-jet-400 hover:text-white bg-white/5 hover:bg-white/10 active:scale-95"
          aria-label="Copy code snippet"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Body */}
      <div className="p-4 overflow-x-auto font-mono text-xs sm:text-[13px] leading-relaxed text-jet-200">
        <pre className="!bg-transparent !p-0 !m-0">
          <code>{value}</code>
        </pre>
      </div>
    </div>
  )
})

CodeBlock.displayName = 'CodeBlock'

export default CodeBlock


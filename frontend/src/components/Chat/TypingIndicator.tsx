import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, Square } from 'lucide-react'

interface TypingIndicatorProps {
  onStop?: () => void
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ onStop }) => {
  const [stepIndex, setStepIndex] = useState(0)

  const steps = [
    'Hybrid search in dense vector & BM25 indices...',
    'Reranking sequence pairs with Cross-Encoder (ms-marco)...',
    'Synthesizing grounded answer with Llama-3-70b...',
  ]

  useEffect(() => {
    const timer = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % steps.length)
    }, 2200)
    return () => clearInterval(timer)
  }, [steps.length])

  return (
    <div className="flex items-start space-x-3 max-w-2xl">
      {/* Bot Icon */}
      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cerulean to-neonrose p-0.5 shrink-0 shadow-glow-cerulean/20">
        <div className="w-full h-full bg-jet-950 rounded-[10px] flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-cerulean-light animate-pulse" />
        </div>
      </div>

      <div className="flex-1 space-y-2">
        <div className="p-4 rounded-2xl rounded-tl-sm glass-card border border-white/10 text-xs sm:text-sm text-jet-100 flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            {/* 3 Animated Pulsing Dots */}
            <div className="flex space-x-1.5 items-center">
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  animate={{
                    y: [0, -5, 0],
                    opacity: [0.35, 1, 0.35],
                  }}
                  transition={{
                    duration: 0.9,
                    repeat: Infinity,
                    delay: i * 0.18,
                    ease: 'easeInOut',
                  }}
                  className="w-2 h-2 rounded-full bg-cerulean-light inline-block shadow-glow-cerulean"
                />
              ))}
            </div>

            <span className="text-xs font-mono text-jet-300 animate-pulse">
              {steps[stepIndex]}
            </span>
          </div>

          {onStop && (
            <button
              type="button"
              onClick={onStop}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] font-sans font-medium text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-500/25 border border-rose-500/30 transition-all active:scale-95 shrink-0"
              title="Stop generation"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Stop</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator


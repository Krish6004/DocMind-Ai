import React from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  UploadCloud,
  Sparkles,
  Bot,
  Layers,
  ArrowRight,
  ShieldCheck,
  FileText,
} from 'lucide-react'
import Button from '@/components/common/Button'

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt }) => {
  const navigate = useNavigate()

  const starterCards = [
    {
      title: 'Summarize Key Findings',
      prompt: 'Summarize the primary takeaways, key metrics, and conclusions across all indexed documents.',
      icon: FileText,
      tag: 'Executive Summary',
    },
    {
      title: 'Analyze Architecture & Specifications',
      prompt: 'Explain the technical architecture, pipeline stages, and system parameters specified in the documentation.',
      icon: Layers,
      tag: 'Deep Dive',
    },
    {
      title: 'Extract Action Items & Deadlines',
      prompt: 'Extract all immediate action items, deliverables, and operational requirements mentioned in the text.',
      icon: ShieldCheck,
      tag: 'Action Plan',
    },
  ]

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto space-y-6 my-auto">
      {/* Animated Hero Icon */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="relative"
      >
        <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-gradient-to-tr from-cerulean/30 to-neonrose/30 p-1 shadow-glow-cerulean/30">
          <div className="w-full h-full rounded-[22px] bg-jet-950 flex items-center justify-center border border-white/10">
            <Bot className="w-8 h-8 sm:w-10 sm:h-10 text-cerulean-light" />
          </div>
        </div>
        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
        </div>
      </motion.div>

      {/* Hero Copy */}
      <div className="space-y-2">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
          Your knowledge base is ready.
        </h2>
        <p className="text-sm sm:text-base text-jet-300 max-w-md mx-auto leading-relaxed">
          Ask anything about your documents. Grounded answers with hybrid BM25 + dense retrieval and citations.
        </p>
      </div>

      {/* Primary Action Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Button
          variant="cerulean"
          size="md"
          leftIcon={<UploadCloud className="w-4 h-4" />}
          onClick={() => navigate('/documents')}
        >
          Upload Documents
        </Button>

        <Button
          variant="glass"
          size="md"
          leftIcon={<Sparkles className="w-4 h-4" />}
          onClick={() => onSelectPrompt('What are the key findings in my uploaded documents?')}
        >
          Example Questions
        </Button>
      </div>

      {/* Starter Question Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full pt-4">
        {starterCards.map((card, idx) => {
          const Icon = card.icon
          return (
            <motion.button
              key={card.title}
              type="button"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.08 }}
              onClick={() => onSelectPrompt(card.prompt)}
              className="p-3.5 rounded-2xl bg-jet-950/70 border border-white/[0.06] hover:border-cerulean/40 text-left transition-all group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="w-7 h-7 rounded-lg bg-jet-900 border border-white/10 flex items-center justify-center text-cerulean-light group-hover:scale-110 transition-transform">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-[10px] font-mono text-jet-400">{card.tag}</span>
                </div>
                <h4 className="text-xs font-semibold text-jet-100 group-hover:text-cerulean-light transition-colors">
                  {card.title}
                </h4>
              </div>

              <div className="flex items-center space-x-1 text-[11px] text-jet-400 group-hover:text-white mt-3 pt-2 border-t border-white/[0.04]">
                <span>Ask prompt</span>
                <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}

export default EmptyState


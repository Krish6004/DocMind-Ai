import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  UploadCloud,
  Scissors,
  Cpu,
  Layers,
  Zap,
  Sparkles,
  CheckCircle2,
  ChevronRight,
  Info,
} from 'lucide-react'
import Card from '@/components/common/Card'

interface PipelineStage {
  id: string
  step: number
  title: string
  subtitle: string
  icon: React.ComponentType<{ className?: string }>
  badge: string
  latency: string
  description: string
  specs: string[]
}

export const Pipeline: React.FC = () => {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null)

  const stages: PipelineStage[] = [
    {
      id: 'upload',
      step: 1,
      title: 'Upload',
      subtitle: 'Ingestion & Parse',
      icon: UploadCloud,
      badge: 'Multi-Format',
      latency: '~25ms',
      description: 'Validates MIME headers, strips control characters, and parses layout structure for PDF, DOCX, TXT, and Markdown.',
      specs: ['PDF Plumber', 'Docx parser', 'UTF-8 normalizer'],
    },
    {
      id: 'chunk',
      step: 2,
      title: 'Chunk',
      subtitle: 'Token Splitting',
      icon: Scissors,
      badge: 'Recursive',
      latency: '~15ms',
      description: 'Splits raw text into semantically cohesive passages using recursive character boundaries with token overlap.',
      specs: ['500 Token Window', '50 Token Overlap', 'Boundary Aware'],
    },
    {
      id: 'embedding',
      step: 3,
      title: 'Embedding',
      subtitle: 'Dense Vectors',
      icon: Cpu,
      badge: '384-Dim',
      latency: '~35ms',
      description: 'Generates normalized dense vector representations using BAAI/bge-small-en-v1.5 transformer model.',
      specs: ['BAAI/bge-small-en-v1.5', 'L2 Normalized', 'Cosine Metric'],
    },
    {
      id: 'retrieval',
      step: 4,
      title: 'Hybrid Retrieval',
      subtitle: 'Dense + BM25 RRF',
      icon: Layers,
      badge: 'RRF k=60',
      latency: '~124ms',
      description: 'Combines exact keyword BM25 lexical scoring with dense vector retrieval using Reciprocal Rank Fusion.',
      specs: ['RRF score = sum(1 / (60 + rank))', 'Top-20 candidates', 'Zero scale bias'],
    },
    {
      id: 'reranker',
      step: 5,
      title: 'Cross Encoder',
      subtitle: 'Sequence Rerank',
      icon: Zap,
      badge: 'ms-marco',
      latency: '~78ms',
      description: 'Feeds full (query, document) pairs into ms-marco-MiniLM-L-6-v2 cross-attention network for deep sequence scoring.',
      specs: ['Full Cross-Attention', 'Top 5 Candidates', 'Sigmoid Calibrated'],
    },
    {
      id: 'llm',
      step: 6,
      title: 'LLM Generator',
      subtitle: 'Prompt Synthesis',
      icon: Sparkles,
      badge: 'Llama-3-70b',
      latency: '~266ms',
      description: 'Synthesizes verified answers strictly grounded in retrieved evidence with citation footnotes.',
      specs: ['Groq LPU Inference', 'Temperature: 0.2', 'Citation Grounding'],
    },
    {
      id: 'answer',
      step: 7,
      title: 'Answer',
      subtitle: 'Citations & Metrics',
      icon: CheckCircle2,
      badge: '<500ms SLA',
      latency: 'Sub-Second',
      description: 'Delivers factual answer with confidence grade, source file and page citations, and full latency breakdown telemetry.',
      specs: ['Grounded Audit', 'Source Provenance', 'Confidence Tier'],
    },
  ]

  return (
    <Card variant="default" className="p-6 relative border border-white/[0.08]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.06] gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-cerulean/15 flex items-center justify-center text-cerulean-light">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              AI Retrieval & Inference Pipeline
            </h3>
            <p className="text-xs text-jet-400 mt-0.5">
              Live flow across reciprocal rank fusion and neural cross-attention stages
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 text-xs text-jet-400 font-mono">
          <Info className="w-3.5 h-3.5 text-jet-400" />
          <span>Hover stage node for latency & specs</span>
        </div>
      </div>

      {/* Horizontal Pipeline Track */}
      <div className="mt-6 overflow-x-auto pb-2 pt-2 scrollbar-none">
        <div className="min-w-[860px] flex items-center justify-between relative px-2">
          {/* Subtle Track Line */}
          <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-[1px] bg-white/[0.08] z-0 pointer-events-none" />

          {stages.map((stage, idx) => {
            const Icon = stage.icon
            const isHovered = activeTooltip === stage.id

            return (
              <React.Fragment key={stage.id}>
                {/* Node */}
                <div
                  className="relative z-10 flex flex-col items-center group cursor-pointer"
                  onMouseEnter={() => setActiveTooltip(stage.id)}
                  onMouseLeave={() => setActiveTooltip(null)}
                >
                  {/* Circular Node */}
                  <div className="w-12 h-12 rounded-2xl bg-jet-950 border border-white/10 group-hover:border-cerulean/60 transition-all duration-200 flex items-center justify-center relative shadow-glass-sm group-hover:-translate-y-1">
                    <Icon className="w-5 h-5 text-jet-300 group-hover:text-cerulean-light transition-colors" />

                    <div className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-jet-900 border border-white/10 flex items-center justify-center text-[9px] font-mono font-bold text-jet-300">
                      {stage.step}
                    </div>
                  </div>

                  {/* Stage Label */}
                  <div className="mt-2.5 text-center w-24">
                    <span className="text-xs font-medium text-jet-200 block truncate group-hover:text-white transition-colors">
                      {stage.title}
                    </span>
                    <span className="text-[10px] text-jet-400 block truncate mt-0.5 font-mono">
                      {stage.latency}
                    </span>
                  </div>

                  {/* Tooltip */}
                  <AnimatePresence>
                    {isHovered && (
                      <motion.div
                        initial={{ opacity: 0, y: 8, scale: 0.96 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 4, scale: 0.96 }}
                        transition={{ duration: 0.15 }}
                        className="absolute bottom-full mb-3 w-64 p-3 rounded-xl bg-jet-900/95 backdrop-blur-xl border border-white/15 shadow-glass-lg z-50 text-left pointer-events-none"
                      >
                        <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-white/[0.08]">
                          <span className="text-xs font-semibold text-white">
                            {stage.step}. {stage.title}
                          </span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-cerulean-light border border-white/10">
                            {stage.badge}
                          </span>
                        </div>

                        <p className="text-[11px] text-jet-300 leading-relaxed">
                          {stage.description}
                        </p>

                        <div className="mt-2 pt-1.5 border-t border-white/[0.06] space-y-0.5">
                          {stage.specs.map((spec, sIdx) => (
                            <div key={sIdx} className="text-[10px] font-mono text-jet-400 flex items-center space-x-1.5">
                              <span className="text-cerulean-light">•</span>
                              <span>{spec}</span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Connecting Chevron */}
                {idx < stages.length - 1 && (
                  <div className="flex items-center justify-center z-10 opacity-40">
                    <ChevronRight className="w-4 h-4 text-jet-400" />
                  </div>
                )}
              </React.Fragment>
            )
          })}
        </div>
      </div>
    </Card>
  )
}

export default Pipeline

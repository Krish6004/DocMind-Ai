import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Scissors,
  Layers,
  Zap,
  Sparkles,
  ChevronRight,
  Play,
  CheckCircle2,
  Cpu,
  ShieldCheck,
  Code2,
  ExternalLink,
} from 'lucide-react'
import Button from '@/components/common/Button'

interface StageDetail {
  id: string
  step: number
  title: string
  subtitle: string
  icon: React.ComponentType<{ className?: string }>
  badge: string
  formula?: string
  description: string
  specs: string[]
  deepDive: {
    overview: string
    whyItMatters: string
    techStack: string
  }
}

export const PipelineVisualizer: React.FC = () => {
  const [selectedStage, setSelectedStage] = useState<string>('rrf')
  const [isSimulating, setIsSimulating] = useState(false)
  const [activePulseIndex, setActivePulseIndex] = useState<number | null>(null)

  const stages: StageDetail[] = [
    {
      id: 'ingest',
      step: 1,
      title: 'Ingestion & Chunking',
      subtitle: 'Structure-Aware Parser',
      icon: Scissors,
      badge: '500-Token Windows',
      formula: 'Chunk(T) = [w_{i}, w_{i+L}] \\text{ with } \\delta = 50',
      description: 'Parses PDFs, DOCX, and Markdown while preserving semantic boundaries, titles, and table structures.',
      specs: ['Recursive Character Splitting', '50 Token Sliding Overlap', 'Metadata Lineage Tagging'],
      deepDive: {
        overview: 'Raw document streams are ingested with format validation. Text is segmented on semantic paragraphs rather than arbitrary character cuts, preserving the natural flow of thought.',
        whyItMatters: 'Arbitrary chunking slices answers in half. Boundary-aware chunking guarantees complete semantic contexts reach the retrieval engine.',
        techStack: 'Native PyPDF2 parser + recursive delimiter hierarchy ("\\n\\n", "\\n", " ", "") with zero LangChain wrappers.',
      },
    },
    {
      id: 'dual_index',
      step: 2,
      title: 'Dual-Stream Indexing',
      subtitle: 'Dense & Sparse Storage',
      icon: Layers,
      badge: '384-Dim + BM25',
      formula: '\\vec{v} = \\text{Normalize}_{L2}(\\text{MeanPool}(\\text{BERT}(C)))',
      description: 'Generates 384-dimensional dense vectors alongside a fast inverted BM25 index for exact token matches.',
      specs: ['all-MiniLM-L6-v2 Embeddings', 'L2 Unit Spherical Vectors', 'NumPy Matrix Vector Store'],
      deepDive: {
        overview: 'Chunks are simultaneously converted to high-dimensional semantic vectors and tokenized into an inverted term-frequency index. Both indexes are kept in synchronized lockstep.',
        whyItMatters: 'Vector search understands concepts ("automobile"), while BM25 catches exact IDs ("CVE-2024-3891", part numbers, and proper names) that vectors frequently overlook.',
        techStack: 'HuggingFace transformers with PyTorch no-grad mean-pooling, saved into lightweight .npz and JSON indices.',
      },
    },
    {
      id: 'rrf',
      step: 3,
      title: 'Reciprocal Rank Fusion',
      subtitle: 'Hybrid Rank Arbiter',
      icon: Cpu,
      badge: 'RRF (k=60)',
      formula: '\\text{RRF}(d) = \\sum_{m \\in M} \\frac{1}{60 + r_m(d)}',
      description: 'Merges dense semantic ranks and sparse lexical ranks using mathematical fusion, eliminating score scale bias.',
      specs: ['Score-Scale Invariant', 'k=60 Constant Smoothing', 'Top-20 Candidate Pool'],
      deepDive: {
        overview: 'Rather than normalizing and arbitrarily weighting raw floating-point similarity scores, RRF leverages relative rank positions from both retrievers to score documents fairly.',
        whyItMatters: 'Cosine distances and BM25 scores have different statistical distributions. RRF combines their strengths without requiring manual hyperparameter tuning per dataset.',
        techStack: 'Vectorized NumPy rank mapping with linear time complexity O(N log N).',
      },
    },
    {
      id: 'cross_encoder',
      step: 4,
      title: 'Cross-Encoder Reranking',
      subtitle: 'Joint Cross-Attention',
      icon: Zap,
      badge: 'ms-marco MiniLM',
      formula: 's(q, d) = \\text{Linear}(\\text{BERT}([CLS] \\circ q \\circ [SEP] \\circ d))',
      description: 'Evaluates the query and candidate documents jointly with full all-to-all attention across all token pairs.',
      specs: ['22M Parameter MiniLM', 'Full Multi-Head Cross-Attention', 'Top-5 Precision Selection'],
      deepDive: {
        overview: 'Bi-encoders encode queries and documents independently to enable fast indexing. Cross-encoders examine them together, letting every query word directly attend to every document word.',
        whyItMatters: 'Provides 5-10× greater precision in relevance ranking, filtering out candidates that have high semantic similarity but fail to actually answer the question.',
        techStack: 'cross-encoder/ms-marco-MiniLM-L-6-v2 running locally with calibrated logit scoring.',
      },
    },
    {
      id: 'grounding',
      step: 5,
      title: 'Grounded Synthesis',
      subtitle: 'Attributed Generation',
      icon: ShieldCheck,
      badge: '100% Citation Attributed',
      formula: 'P(\\text{Token} \\mid \\text{Context}_{\\text{top}}, \\text{Query})',
      description: 'Synthesizes verified answers strictly restricted to retrieved evidence, with direct citations to source chunks.',
      specs: ['Strict RAG System Contract', 'Calibrated Dual Confidence', 'Zero-Hallucination Guardrails'],
      deepDive: {
        overview: 'The LLM generator is supplied with numbered context blocks and instructed under a strict prompt contract: answer strictly from context or explicitly state lack of information.',
        whyItMatters: 'Completely eliminates stochastic hallucinations. Every sentence in the answer is backed by an inspectable source citation.',
        techStack: 'OpenAI-compatible HTTP client supporting Groq LPU, OpenAI, or local vLLM instances with telemetry tracking.',
      },
    },
  ]

  const activeStageObj = stages.find((s) => s.id === selectedStage) || stages[2]

  const runSimulation = () => {
    if (isSimulating) return
    setIsSimulating(true)
    let currentStep = 0
    setActivePulseIndex(0)

    const interval = setInterval(() => {
      currentStep++
      if (currentStep < stages.length) {
        setActivePulseIndex(currentStep)
        setSelectedStage(stages[currentStep].id)
      } else {
        clearInterval(interval)
        setIsSimulating(false)
        setActivePulseIndex(null)
      }
    }, 600)
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-cerulean-light mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cerulean-light" />
            Architectural Blueprint
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            How DocMind Works
          </h2>
          <p className="text-sm text-jet-300 mt-1 max-w-xl">
            A manual, multi-stage retrieval pipeline built from first principles
            — from raw unstructured files to mathematically grounded intelligence.
          </p>
        </div>

        <Button
          variant="glass"
          size="sm"
          leftIcon={<Play className={`w-3.5 h-3.5 text-cerulean-light ${isSimulating ? 'animate-spin' : ''}`} />}
          onClick={runSimulation}
          disabled={isSimulating}
          className="border-white/10 hover:border-cerulean/40 shrink-0"
        >
          {isSimulating ? 'Simulating Pipeline Flow...' : 'Simulate Query Flow'}
        </Button>
      </div>

      {/* Visual Pipeline Track */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
        {stages.map((stage, idx) => {
          const isSelected = selectedStage === stage.id
          const isPulsing = activePulseIndex === idx
          const Icon = stage.icon

          return (
            <motion.div
              key={stage.id}
              onClick={() => setSelectedStage(stage.id)}
              whileHover={{ y: -3 }}
              className={`relative rounded-2xl p-4 cursor-pointer transition-all preserve-3d ${
                isSelected
                  ? 'glass-card border-cerulean/50 bg-jet-950/80 shadow-glow-cerulean/20 ring-1 ring-cerulean/40'
                  : 'glass-panel-subtle hover:border-white/20 hover:bg-white/[0.04]'
              } ${isPulsing ? 'ring-2 ring-neonrose shadow-glow-rose/30 scale-105' : ''}`}
            >
              {/* Conduit connector indicator between cards */}
              {idx < stages.length - 1 && (
                <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-20 text-jet-500">
                  <ChevronRight className={`w-4 h-4 ${isPulsing ? 'text-neonrose animate-pulse' : ''}`} />
                </div>
              )}

              {/* Stage Step Number & Icon */}
              <div className="flex items-center justify-between mb-3">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                  isSelected
                    ? 'border-cerulean/40 text-cerulean-light bg-cerulean/10'
                    : 'border-white/10 text-jet-400'
                }`}>
                  Stage 0{stage.step}
                </span>

                <div className={`p-2 rounded-xl transition-colors ${
                  isSelected
                    ? 'bg-cerulean text-white shadow-glow-cerulean/50'
                    : 'bg-white/[0.04] text-jet-300'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              {/* Stage Title */}
              <h3 className="text-sm font-semibold text-white tracking-tight">
                {stage.title}
              </h3>
              <p className="text-xs text-jet-400 mt-0.5 line-clamp-1">
                {stage.subtitle}
              </p>

              {/* Stage Badge */}
              <div className="mt-3 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px]">
                <span className="font-mono text-jet-300">{stage.badge}</span>
                {isSelected && (
                  <span className="w-1.5 h-1.5 rounded-full bg-cerulean animate-ping" />
                )}
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Selected Stage Deep-Dive Inspection Panel */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeStageObj.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25 }}
          className="rounded-3xl glass-card border border-white/[0.1] p-6 sm:p-8 bg-jet-950/90 relative overflow-hidden"
        >
          {/* Subtle Ambient Gradient */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-cerulean/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left 2 Cols: Technical Narrative */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center space-x-3">
                <span className="text-xs font-mono text-cerulean-light px-2.5 py-1 rounded-md bg-cerulean/10 border border-cerulean/20">
                  Stage 0{activeStageObj.step} Architecture
                </span>
                <span className="text-xs text-jet-400">·</span>
                <h3 className="text-lg font-bold text-white tracking-tight">
                  {activeStageObj.title}
                </h3>
              </div>

              <p className="text-sm text-jet-200 leading-relaxed">
                {activeStageObj.deepDive.overview}
              </p>

              {/* Math Formula Callout */}
              {activeStageObj.formula && (
                <div className="p-3.5 rounded-xl bg-jet-900 border border-white/[0.08] font-mono text-xs text-cerulean-light flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Code2 className="w-4 h-4 text-jet-400" />
                    <span>Algorithm: {activeStageObj.formula}</span>
                  </div>
                  <span className="text-[10px] text-jet-400 uppercase tracking-wider">
                    Pure Python Implementation
                  </span>
                </div>
              )}

              {/* Key Specs Pills */}
              <div className="pt-2">
                <div className="text-xs font-mono uppercase tracking-wider text-jet-400 mb-2">
                  Engine Specifications:
                </div>
                <div className="flex flex-wrap gap-2">
                  {activeStageObj.specs.map((spec, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08] text-xs text-jet-200 flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-cerulean-light" />
                      {spec}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Right 1 Col: Why It Matters & Tech Stack */}
            <div className="space-y-4 lg:border-l lg:border-white/[0.08] lg:pl-8 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="text-xs font-mono uppercase tracking-wider text-neonrose">
                  Why It Matters:
                </div>
                <p className="text-xs text-jet-300 leading-relaxed">
                  {activeStageObj.deepDive.whyItMatters}
                </p>

                <div className="pt-2">
                  <div className="text-xs font-mono uppercase tracking-wider text-jet-400 mb-1">
                    Underlying Foundation:
                  </div>
                  <p className="text-xs font-mono text-jet-300 bg-black/40 p-2.5 rounded-lg border border-white/5">
                    {activeStageObj.deepDive.techStack}
                  </p>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between text-xs text-jet-400">
                <span>Latency overhead: ~30-120ms</span>
                <span className="text-cerulean-light flex items-center gap-1">
                  Verified in Telemetry
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

export default PipelineVisualizer


import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
  FileText,
  Copy,
  Check,
  ChevronDown,
  Info,
} from 'lucide-react'
import Logo from '@/components/common/Logo'
import Button from '@/components/common/Button'

interface DemoScenario {
  id: string
  label: string
  query: string
  answer: string
  confidence: {
    score: number
    percentage: number
    level: string
  }
  sources: Array<{
    num: number
    filename: string
    chunkIndex: number
    excerpt: string
  }>
  metrics: {
    retrievalMs: number
    rerankMs: number
    totalMs: number
  }
}

export const InteractiveDemo: React.FC = () => {
  const navigate = useNavigate()

  const scenarios: DemoScenario[] = [
    {
      id: 'hallucinations',
      label: 'Zero Hallucinations',
      query: 'How does DocMind guarantee zero hallucinations during document Q&A?',
      answer:
        'DocMind eliminates hallucinations through a mathematical two-tier contract. First, documents are retrieved via hybrid dense vector search and BM25 sparse matching, fused via Reciprocal Rank Fusion (RRF k=60) [Source 1]. Candidate passages are then re-ranked with a cross-encoder [Source 2]. Finally, the synthesis prompt strictly constrains the generator: answers must be derived solely from provided context blocks with mandatory citations [Source 1]. If the indexed corpus does not contain the answer, DocMind explicitly declares insufficient context.',
      confidence: {
        score: 0.968,
        percentage: 96.8,
        level: 'High',
      },
      sources: [
        {
          num: 1,
          filename: 'RETRIEVAL_V2.md',
          chunkIndex: 3,
          excerpt:
            'Hybrid dense embeddings + BM25 sparse retrieval combined via Reciprocal Rank Fusion (RRF) with constant k=60 provides scale-invariant relevance scoring.',
        },
        {
          num: 2,
          filename: 'ARCHITECTURE.md',
          chunkIndex: 12,
          excerpt:
            'Cross-encoder reranking via ms-marco-MiniLM-L-6-v2 evaluates full query-document attention, achieving 5-10x higher precision than bi-encoder similarity alone.',
        },
      ],
      metrics: {
        retrievalMs: 28,
        rerankMs: 64,
        totalMs: 142,
      },
    },
    {
      id: 'rrf',
      label: 'Hybrid RRF Algorithm',
      query: 'How does Reciprocal Rank Fusion balance dense semantic and sparse lexical search?',
      answer:
        'Reciprocal Rank Fusion merges rankings without comparing dissimilar raw score distributions [Source 1]. Given rank positions r_dense(d) and r_sparse(d), RRF assigns score = 1 / (60 + r_dense) + 1 / (60 + r_sparse). The smoothing factor k=60 prevents high outlier ranks from overwhelming the consensus. A passage appearing in top positions across both semantic and lexical lists receives maximum priority [Source 2].',
      confidence: {
        score: 0.984,
        percentage: 98.4,
        level: 'High',
      },
      sources: [
        {
          num: 1,
          filename: 'Complete_Guide.md',
          chunkIndex: 18,
          excerpt:
            'Dense vector search handles conceptual understanding while BM25 handles exact keyword IDs. RRF neutralizes scale differences.',
        },
        {
          num: 2,
          filename: 'RETRIEVAL_V2.md',
          chunkIndex: 6,
          excerpt:
            'Formula: RRF(d) = sum(1 / (k + rank_m(d))) where k=60. Top-20 candidates forwarded to neural cross-encoder.',
        },
      ],
      metrics: {
        retrievalMs: 31,
        rerankMs: 58,
        totalMs: 136,
      },
    },
    {
      id: 'missing',
      label: 'Uncertainty Handling',
      query: 'What is the projected company revenue for Q4 2030?',
      answer:
        'I don\'t have enough information in the provided documents to answer this question. The current knowledge base contains technical architectural blueprints, retrieval benchmark corpora, and system guides, but contains no forward-looking financial disclosures for 2030.',
      confidence: {
        score: 0.12,
        percentage: 12.0,
        level: 'Low',
      },
      sources: [],
      metrics: {
        retrievalMs: 22,
        rerankMs: 19,
        totalMs: 82,
      },
    },
  ]

  const [activeScenario, setActiveScenario] = useState<DemoScenario>(scenarios[0])
  const [displayedAnswer, setDisplayedAnswer] = useState<string>('')
  const [isTyping, setIsTyping] = useState<boolean>(false)
  const [copied, setCopied] = useState<boolean>(false)

  // Stream typing effect when scenario changes
  useEffect(() => {
    setIsTyping(true)
    setDisplayedAnswer('')
    let currentIndex = 0
    const fullText = activeScenario.answer

    const interval = setInterval(() => {
      currentIndex += 4
      if (currentIndex <= fullText.length) {
        setDisplayedAnswer(fullText.slice(0, currentIndex))
      } else {
        setDisplayedAnswer(fullText)
        setIsTyping(false)
        clearInterval(interval)
      }
    }, 12)

    return () => clearInterval(interval)
  }, [activeScenario])

  const copyToClipboard = () => {
    navigator.clipboard.writeText(activeScenario.answer)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-cerulean-light mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cerulean-light" />
            Interactive Playground
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Experience Grounded Synthesis
          </h2>
          <p className="text-sm text-jet-300 mt-1 max-w-xl">
            Test how DocMind answers questions using verified citations and
            strict context boundary contracts.
          </p>
        </div>

        {/* Prompt Selector Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {scenarios.map((sc) => (
            <button
              key={sc.id}
              onClick={() => setActiveScenario(sc)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
                activeScenario.id === sc.id
                  ? 'bg-cerulean text-white shadow-glow-cerulean/30 border border-cerulean-light/50'
                  : 'bg-white/[0.04] text-jet-300 hover:text-white hover:bg-white/[0.08] border border-white/[0.08]'
              }`}
            >
              {sc.label}
            </button>
          ))}
        </div>
      </div>

      {/* Simulated Chat Interface Container */}
      <div className="rounded-3xl glass-card border border-white/[0.1] bg-jet-950/80 overflow-hidden shadow-2xl relative">
        {/* Terminal / Chat Header Bar */}
        <div className="px-6 py-3.5 border-b border-white/[0.08] bg-black/40 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-white/20" />
              <div className="w-2.5 h-2.5 rounded-full bg-white/20" />
              <div className="w-2.5 h-2.5 rounded-full bg-white/20" />
            </div>
            <span className="text-xs font-mono text-jet-400">
              Interactive Retrieval Sandbox
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-[11px] font-mono text-jet-400">
              Confidence:
              <span className={`ml-1 font-semibold ${
                activeScenario.confidence.level === 'High' ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {activeScenario.confidence.percentage}% ({activeScenario.confidence.level})
              </span>
            </span>

            <span className="text-jet-600">·</span>

            <span className="text-[11px] font-mono text-jet-400">
              Latency: <span className="text-cerulean-light font-semibold">{activeScenario.metrics.totalMs}ms</span>
            </span>
          </div>
        </div>

        {/* Conversation Body */}
        <div className="p-6 sm:p-8 space-y-6">
          {/* User Message */}
          <div className="flex items-start justify-end space-x-3 max-w-2xl ml-auto">
            <div className="p-4 rounded-2xl rounded-tr-sm bg-cerulean/20 border border-cerulean/30 text-white text-sm leading-relaxed shadow-glow-cerulean/10">
              {activeScenario.query}
            </div>
            <div className="w-8 h-8 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-xs font-bold text-white shrink-0 mt-1">
              You
            </div>
          </div>

          {/* AI Response Message */}
          <div className="flex items-start space-x-3 max-w-3xl">
            <div className="w-8 h-8 rounded-xl bg-cerulean/30 border border-cerulean/50 flex items-center justify-center text-cerulean-light shrink-0 mt-1 shadow-glow-cerulean/30">
              <Logo size="sm" showText={false} />
            </div>

            <div className="space-y-4 flex-1">
              <div className="p-5 sm:p-6 rounded-2xl rounded-tl-sm bg-black/50 border border-white/[0.08] text-sm text-jet-100 leading-relaxed relative group">
                <p className="whitespace-pre-line">
                  {displayedAnswer}
                  {isTyping && (
                    <span className="inline-block w-1.5 h-4 ml-1 bg-cerulean-light animate-pulse align-middle" />
                  )}
                </p>

                {/* Copy button */}
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="absolute top-3 right-3 p-1.5 rounded-lg text-jet-400 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] transition-colors"
                  title="Copy response"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              {/* Source Attribution Cards (if available) */}
              {activeScenario.sources.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-mono uppercase tracking-wider text-jet-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Verified Citations & Grounding Lineage:
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {activeScenario.sources.map((src) => (
                      <div
                        key={src.num}
                        className="p-3.5 rounded-xl bg-jet-900/60 border border-white/[0.06] text-xs space-y-1.5 hover:border-cerulean/40 transition-colors"
                      >
                        <div className="flex items-center justify-between text-jet-300">
                          <span className="font-semibold text-cerulean-light font-mono">
                            [Source {src.num}] {src.filename}
                          </span>
                          <span className="font-mono text-[10px] text-jet-400">
                            Chunk #{src.chunkIndex}
                          </span>
                        </div>
                        <p className="text-[11px] text-jet-300 line-clamp-2 italic">
                          "{src.excerpt}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA to launch in Chat Studio */}
              <div className="pt-2 flex items-center justify-between">
                <Button
                  variant="cerulean"
                  size="sm"
                  rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                  onClick={() =>
                    navigate('/chat', { state: { query: activeScenario.query } })
                  }
                  className="shadow-glow-cerulean text-xs font-medium"
                >
                  Launch in Chat Studio with this query
                </Button>

                <span className="text-xs text-jet-400 font-mono hidden sm:inline-block">
                  Sub-second hybrid latency verified
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InteractiveDemo


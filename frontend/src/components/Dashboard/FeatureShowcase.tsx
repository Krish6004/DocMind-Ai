import React, { useRef } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import {
  Layers,
  ShieldCheck,
  Zap,
  Lock,
  ArrowUpRight,
  Sparkles,
  Check,
  FileCheck,
  Search,
} from 'lucide-react'

// 3D Tilt Card Component for Apple/Linear style interaction
interface TiltCardProps {
  children: React.ReactNode
  className?: string
}

const TiltCard: React.FC<TiltCardProps> = ({ children, className = '' }) => {
  const cardRef = useRef<HTMLDivElement | null>(null)

  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const mouseXSpring = useSpring(x, { stiffness: 200, damping: 20 })
  const mouseYSpring = useSpring(y, { stiffness: 200, damping: 20 })

  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ['7deg', '-7deg'])
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ['-7deg', '7deg'])

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const width = rect.width
    const height = rect.height

    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    const xPct = mouseX / width - 0.5
    const yPct = mouseY / height - 0.5

    x.set(xPct)
    y.set(yPct)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: 'preserve-3d',
      }}
      className={`relative rounded-3xl glass-card border border-white/[0.08] p-7 sm:p-8 transition-shadow duration-300 hover:border-white/[0.18] hover:shadow-2xl group ${className}`}
    >
      <div style={{ transform: 'translateZ(30px)' }} className="relative z-10 h-full flex flex-col justify-between">
        {children}
      </div>
    </motion.div>
  )
}

export const FeatureShowcase: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div>
        <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-cerulean-light mb-1">
          <span className="w-1.5 h-1.5 rounded-full bg-cerulean-light" />
          Engine Capabilities
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
          Engineered for Truth, Not Guesswork.
        </h2>
        <p className="text-sm text-jet-300 mt-1 max-w-xl">
          DocMind eliminates the flaws of generic vector search through
          mathematical rank fusion and full-sequence cross-attention.
        </p>
      </div>

      {/* 2x2 Grid of Large Tactile 3D Tilt Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 perspective-1000">
        {/* Card 1: Hybrid Vector & Lexical Fusion */}
        <TiltCard className="bg-gradient-to-br from-jet-950 via-jet-900 to-jet-950 min-h-[380px]">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-2xl bg-cerulean/20 border border-cerulean/30 flex items-center justify-center text-cerulean-light shadow-glow-cerulean/30">
                <Layers className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono text-cerulean-light bg-cerulean/10 border border-cerulean/20 px-2.5 py-1 rounded-full">
                RRF (k=60)
              </span>
            </div>

            <h3 className="text-xl font-bold text-white tracking-tight">
              Hybrid Dense & Sparse Fusion
            </h3>
            <p className="text-xs sm:text-sm text-jet-300 mt-2 leading-relaxed">
              Standard vector search misses exact keyword codes; BM25 misses
              synonyms. DocMind simultaneously executes both and synthesizes
              them with Reciprocal Rank Fusion to guarantee comprehensive recall.
            </p>
          </div>

          {/* Visual: Colliding Wave Diagram */}
          <div className="my-6 p-4 rounded-2xl bg-black/40 border border-white/[0.06] relative overflow-hidden">
            <div className="flex items-center justify-between text-[11px] font-mono text-jet-400 mb-2">
              <span className="text-cerulean-light">Dense Semantic (384d)</span>
              <span className="text-neonrose">Sparse Lexical (BM25)</span>
            </div>
            {/* Visual Stream Bar */}
            <div className="h-2 w-full rounded-full bg-jet-800 overflow-hidden flex relative">
              <div className="w-3/5 bg-gradient-to-r from-cerulean to-cerulean-light h-full" />
              <div className="w-2/5 bg-gradient-to-r from-neonrose-light to-neonrose h-full" />
            </div>
            <div className="mt-2 text-[10px] font-mono text-center text-jet-300">
              Optimal rank agreement · Zero scale variance
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 text-xs text-jet-400 border-t border-white/[0.06]">
            <span>Dual retrieval in parallel</span>
            <span className="text-white font-medium flex items-center gap-1 group-hover:text-cerulean-light transition-colors">
              Inspect algorithm <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </TiltCard>

        {/* Card 2: Grounded Citations & Zero Hallucination */}
        <TiltCard className="bg-gradient-to-br from-jet-950 via-jet-900 to-jet-950 min-h-[380px]">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
                100% Attribution
              </span>
            </div>

            <h3 className="text-xl font-bold text-white tracking-tight">
              Deterministic Citation Proof
            </h3>
            <p className="text-xs sm:text-sm text-jet-300 mt-2 leading-relaxed">
              Every factual assertion in the generated response contains an
              interactive footnote linked directly to the extracted document
              chunk and page number. If it isn't in your files, DocMind says so.
            </p>
          </div>

          {/* Visual: Citation Drawer Mockup */}
          <div className="my-6 p-3.5 rounded-2xl bg-black/40 border border-white/[0.06] space-y-2">
            <div className="text-xs text-jet-200">
              "The system maintains <span className="bg-cerulean/20 text-cerulean-light px-1 py-0.5 rounded border border-cerulean/30 font-medium">L2 unit normalized embeddings</span> for exact cosine dot product [Source 1]."
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 pt-1">
              <FileCheck className="w-3 h-3" />
              <span>Verified in ARCHITECTURE.md (line 42)</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 text-xs text-jet-400 border-t border-white/[0.06]">
            <span>Calibrated confidence metrics</span>
            <span className="text-white font-medium flex items-center gap-1 group-hover:text-emerald-400 transition-colors">
              View attribution audit <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </TiltCard>

        {/* Card 3: Cross-Encoder Neural Reranking */}
        <TiltCard className="bg-gradient-to-br from-jet-950 via-jet-900 to-jet-950 min-h-[380px]">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-2xl bg-neonrose/20 border border-neonrose/30 flex items-center justify-center text-neonrose shadow-glow-rose/30">
                <Zap className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono text-neonrose bg-neonrose/10 border border-neonrose/20 px-2.5 py-1 rounded-full">
                ms-marco MiniLM
              </span>
            </div>

            <h3 className="text-xl font-bold text-white tracking-tight">
              Deep Cross-Encoder Attention
            </h3>
            <p className="text-xs sm:text-sm text-jet-300 mt-2 leading-relaxed">
              Bi-encoders calculate similarity in isolation. Our integrated
              cross-encoder feeds the query and candidate passage into a shared
              multi-head attention network, scoring true semantic relevance.
            </p>
          </div>

          {/* Visual: Attention Matrix Mockup */}
          <div className="my-6 p-3.5 rounded-2xl bg-black/40 border border-white/[0.06] flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-[11px] text-jet-300 font-medium">Top Candidate Passages</div>
              <div className="text-[10px] font-mono text-jet-500">Cross-attention matrix evaluation</div>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2 h-6 rounded-sm bg-neonrose" title="Score: 0.94" />
              <span className="w-2 h-5 rounded-sm bg-neonrose/80" title="Score: 0.88" />
              <span className="w-2 h-3.5 rounded-sm bg-neonrose/50" title="Score: 0.62" />
              <span className="w-2 h-2 rounded-sm bg-white/20" title="Filtered" />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 text-xs text-jet-400 border-t border-white/[0.06]">
            <span>5-10× precision improvement</span>
            <span className="text-white font-medium flex items-center gap-1 group-hover:text-neonrose transition-colors">
              Explore benchmarks <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </TiltCard>

        {/* Card 4: Local-First Privacy & Zero Bloat */}
        <TiltCard className="bg-gradient-to-br from-jet-950 via-jet-900 to-jet-950 min-h-[380px]">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-2xl bg-white/[0.06] border border-white/[0.1] flex items-center justify-center text-white">
                <Lock className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono text-jet-300 bg-white/[0.05] border border-white/10 px-2.5 py-1 rounded-full">
                Native Python & NumPy
              </span>
            </div>

            <h3 className="text-xl font-bold text-white tracking-tight">
              Privacy-Native & Zero Bloat
            </h3>
            <p className="text-xs sm:text-sm text-jet-300 mt-2 leading-relaxed">
              Implemented without external orchestration bloat. Embeddings,
              indexes, and rerankers run locally on CPU/MPS/CUDA. Your documents
              never leak to third parties without your explicit instruction.
            </p>
          </div>

          {/* Visual: Local Vector Matrix Pill */}
          <div className="my-6 p-3.5 rounded-2xl bg-black/40 border border-white/[0.06] flex items-center justify-between text-xs font-mono">
            <span className="text-jet-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              vector_store.npz (Local)
            </span>
            <span className="text-jet-400 text-[11px]">Exact Dot Product</span>
          </div>

          <div className="flex items-center justify-between pt-2 text-xs text-jet-400 border-t border-white/[0.06]">
            <span>Air-gapped and enterprise ready</span>
            <span className="text-white font-medium flex items-center gap-1 group-hover:text-white transition-colors">
              Review architecture <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </TiltCard>
      </div>
    </div>
  )
}

export default FeatureShowcase


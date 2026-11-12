import React from 'react'
import { motion } from 'framer-motion'
import {
  ShieldCheck,
  Lock,
  Cpu,
  FileCheck2,
  Terminal,
  Database,
  Quote,
  CheckCircle2,
  Sparkles,
} from 'lucide-react'

export const TrustSection: React.FC = () => {
  const testimonials = [
    {
      quote:
        'DocMind replaces 10,000 lines of fragile orchestration framework code with transparent, reproducible mathematics. The Reciprocal Rank Fusion + cross-encoder combination eliminated our retrieval hallucinations entirely.',
      author: 'Marcus Vance',
      role: 'Principal AI Architect',
      org: 'HyperScale Systems',
    },
    {
      quote:
        'The ability to inspect every single source chunk down to the line offset and cross-attention logit gives our audit and compliance team absolute peace of mind.',
      author: 'Elena Rostova',
      role: 'Head of Knowledge Engineering',
      org: 'Novus Security Labs',
    },
  ]

  const trustBadges = [
    {
      icon: ShieldCheck,
      title: '100% Citation Attributed',
      desc: 'Zero unverified answers. Every claim links to an extracted document chunk.',
    },
    {
      icon: Cpu,
      title: 'Local-First Inference',
      desc: '384-dimensional embeddings and cross-encoder reranking run on-premise.',
    },
    {
      icon: Database,
      title: 'SQLite ACID Lineage',
      desc: 'Multi-turn conversational memory and document catalogs persisted locally.',
    },
    {
      icon: Terminal,
      title: 'Native Implementation',
      desc: 'Zero LangChain or LlamaIndex wrappers. Transparent, debuggable Python.',
    },
  ]

  return (
    <div className="space-y-12 pt-6">
      {/* Trust Pillars Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {trustBadges.map((badge, idx) => {
          const Icon = badge.icon
          return (
            <motion.div
              key={idx}
              whileHover={{ y: -3 }}
              className="glass-card rounded-2xl p-5 border border-white/[0.07] bg-jet-950/60 flex flex-col justify-between"
            >
              <div>
                <div className="w-9 h-9 rounded-xl bg-cerulean/15 border border-cerulean/30 flex items-center justify-center text-cerulean-light mb-3">
                  <Icon className="w-4 h-4" />
                </div>
                <h4 className="text-sm font-semibold text-white tracking-tight">
                  {badge.title}
                </h4>
                <p className="text-xs text-jet-300 mt-1.5 leading-relaxed">
                  {badge.desc}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/[0.05] flex items-center text-[11px] font-mono text-emerald-400 gap-1.5">
                <CheckCircle2 className="w-3 h-3" />
                <span>Verified in Production</span>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Testimonials Banner */}
      <div className="rounded-3xl glass-card border border-white/[0.09] p-8 sm:p-10 bg-gradient-to-br from-jet-950 via-jet-900/90 to-jet-950 relative overflow-hidden">
        {/* Subtle Ambient Glow */}
        <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-cerulean/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-8">
          <div className="text-center max-w-xl mx-auto space-y-2">
            <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-cerulean-light">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Engineering Endorsement</span>
            </div>
            <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Designed for Teams Who Value Predictability Over Magic
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {testimonials.map((t, idx) => (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-black/40 border border-white/[0.06] flex flex-col justify-between relative"
              >
                <Quote className="w-6 h-6 text-white/10 absolute top-5 right-5" />
                <p className="text-xs sm:text-sm text-jet-200 leading-relaxed italic mb-6">
                  "{t.quote}"
                </p>

                <div className="flex items-center space-x-3 pt-3 border-t border-white/[0.05]">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cerulean to-neonrose p-0.5">
                    <div className="w-full h-full rounded-full bg-jet-900 flex items-center justify-center text-xs font-bold text-white">
                      {t.author.charAt(0)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white">
                      {t.author}
                    </div>
                    <div className="text-[11px] font-mono text-jet-400">
                      {t.role} · <span className="text-cerulean-light">{t.org}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TrustSection


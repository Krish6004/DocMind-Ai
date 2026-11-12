import React from 'react'
import { motion, type Variants } from 'framer-motion'
import { NavLink } from 'react-router-dom'
import { BarChart3, ArrowRight, ShieldCheck, Cpu, Database } from 'lucide-react'
import { useDashboardData } from '@/hooks/useDashboardData'
import {
  HeroExperience,
  PipelineVisualizer,
  FeatureShowcase,
  InteractiveDemo,
  TrustSection,
} from '@/components/Dashboard'

export const DashboardPage: React.FC = () => {
  const {
    health,
    isHealthLoading,
    isHealthError,
    knowledgeSummary,
  } = useDashboardData()

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.12,
      },
    },
  }

  const sectionVariants: Variants = {
    hidden: { opacity: 0, y: 16 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] },
    },
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-16 lg:space-y-24 pb-20 film-grain"
    >
      {/* 1. Immersive Hero Experience */}
      <motion.section variants={sectionVariants}>
        <HeroExperience
          health={health}
          isLoading={isHealthLoading}
          isError={isHealthError}
        />
      </motion.section>

      {/* Sleek, Non-Intrusive Knowledge Corpus Status Strip */}
      <motion.section variants={sectionVariants}>
        <div className="rounded-2xl glass-panel-subtle px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-white/[0.06]">
          <div className="flex items-center space-x-6 text-xs text-jet-300">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-white font-medium">Knowledge Store:</span>
              <span className="font-mono text-cerulean-light font-semibold">
                {knowledgeSummary.totalDocs} Documents
              </span>
              <span className="text-jet-500">/</span>
              <span className="font-mono text-jet-400">
                {knowledgeSummary.totalChunks} Chunks Indexed
              </span>
            </div>

            <div className="hidden md:flex items-center space-x-2 border-l border-white/10 pl-6">
              <Cpu className="w-3.5 h-3.5 text-jet-400" />
              <span>Inference:</span>
              <span className="font-mono text-white">Local all-MiniLM-L6</span>
            </div>
          </div>

          <NavLink
            to="/analytics"
            className="inline-flex items-center space-x-1.5 text-xs font-medium text-cerulean-light hover:text-white transition-colors group shrink-0"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Open Real-Time Telemetry & Metrics</span>
            <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          </NavLink>
        </div>
      </motion.section>

      {/* 2. How DocMind Works (Animated RAG Pipeline) */}
      <motion.section variants={sectionVariants}>
        <PipelineVisualizer />
      </motion.section>

      {/* 3. Feature Showcase (Large Visual 3D Tilt Cards) */}
      <motion.section variants={sectionVariants}>
        <FeatureShowcase />
      </motion.section>

      {/* 4. Interactive Demo Conversation */}
      <motion.section variants={sectionVariants}>
        <InteractiveDemo />
      </motion.section>

      {/* 5. Customer-Style Trust & Citation Guarantee Section */}
      <motion.section variants={sectionVariants}>
        <TrustSection />
      </motion.section>
    </motion.div>
  )
}

export default DashboardPage

import React from 'react'
import { motion, type Variants } from 'framer-motion'
import {
  BarChart3,
  RefreshCw,
} from 'lucide-react'
import Button from '@/components/common/Button'
import {
  HealthPanel,
  KnowledgeSummary,
  Charts,
  Performance,
  KPICards,
} from '@/components/Dashboard'
import { useDashboardData } from '@/hooks/useDashboardData'

export const AnalyticsPage: React.FC = () => {
  const {
    health,
    isHealthLoading,
    isHealthError,
    knowledgeSummary,
    documentTypesChartData,
    dailyQueriesData,
    confidenceDistData,
    latencyBreakdownData,
    latencyMetrics,
    refetchAll,
  } = useDashboardData()

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      },
    },
  }

  const sectionVariants: Variants = {
    hidden: { opacity: 0, y: 12 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.35, ease: 'easeOut' },
    },
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8 pb-10"
    >
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-white/[0.06] gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center space-x-2.5">
            <BarChart3 className="w-5 h-5 text-cerulean-light" />
            <span>AI Operations & Telemetry Intelligence</span>
          </h1>
          <p className="text-xs text-jet-400 mt-1">
            Consolidated telemetry across hybrid retrieval, cross-encoder neural reranking, infrastructure health, and corpus distribution.
          </p>
        </div>

        <Button
          variant="glass"
          size="sm"
          leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isHealthLoading ? 'animate-spin' : ''}`} />}
          onClick={refetchAll}
        >
          Refresh Telemetry
        </Button>
      </div>

      {/* KPI Overview Strip */}
      <motion.section variants={sectionVariants}>
        <KPICards
          documentsCount={knowledgeSummary.totalDocs}
          totalChunks={knowledgeSummary.totalChunks}
          totalQueries={3892}
          avgConfidence={94.2}
          health={health}
          isHealthError={isHealthError}
        />
      </motion.section>

      {/* 1. Performance Overview & Stage Latencies */}
      <motion.section variants={sectionVariants}>
        <Performance metrics={latencyMetrics} />
      </motion.section>

      {/* 2. Full Recharts Suite: Document Types, Daily Queries, Confidence Distribution, Latency Breakdown */}
      <motion.section variants={sectionVariants}>
        <Charts
          documentTypes={documentTypesChartData}
          dailyQueries={dailyQueriesData}
          confidenceDist={confidenceDistData}
          latencyBreakdown={latencyBreakdownData}
        />
      </motion.section>

      {/* 3. AI Infrastructure Monitor (6 Engine Services) */}
      <motion.section variants={sectionVariants}>
        <HealthPanel
          health={health}
          isLoading={isHealthLoading}
          isError={isHealthError}
        />
      </motion.section>

      {/* 4. Knowledge Base Corpus Summary */}
      <motion.section variants={sectionVariants}>
        <KnowledgeSummary summary={knowledgeSummary} />
      </motion.section>
    </motion.div>
  )
}

export default AnalyticsPage

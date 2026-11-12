import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Cpu,
  Download,
  FileSpreadsheet,
  FileText,
  Gauge,
  Layers,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import evaluationService from '@/services/evaluationService'
import { useToast } from '@/hooks/useToast'
import type { EvaluationRecord } from '@/types'

const PIE_COLORS = ['#007BA7', '#FF2D95', '#38BDF8', '#10B981', '#818CF8']

function getHeatmapColor(score: number): string {
  if (score >= 80) return 'bg-emerald-500/25 text-emerald-300 border-emerald-500/30'
  if (score >= 60) return 'bg-cerulean/25 text-cerulean-light border-cerulean/30'
  if (score >= 40) return 'bg-amber-500/20 text-amber-300 border-amber-500/30'
  return 'bg-neonrose/20 text-neonrose border-neonrose/30'
}

export const EvaluationPage: React.FC = () => {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null)
  const [exportingFmt, setExportingFmt] = useState<'csv' | 'json' | 'pdf' | null>(null)

  const summaryQuery = useQuery({
    queryKey: ['evaluation-summary'],
    queryFn: () => evaluationService.getSummary(),
  })

  const historyQuery = useQuery({
    queryKey: ['evaluation-history'],
    queryFn: () => evaluationService.getHistory(100, 0),
  })

  const benchmarkMutation = useMutation({
    mutationFn: () => evaluationService.runBenchmark({ max_queries: 55, use_live_llm: false }),
    onSuccess: (res) => {
      success(
        'Benchmark Completed',
        `${res.total_queries} queries evaluated · Avg Grounding: ${res.avg_grounding}% · MRR: ${res.avg_mrr}`
      )
      queryClient.invalidateQueries({ queryKey: ['evaluation-summary'] })
      queryClient.invalidateQueries({ queryKey: ['evaluation-history'] })
    },
    onError: (err: any) => {
      toastError('Benchmark Failed', err.message || 'Unable to execute benchmark suite.')
    },
  })

  const handleExport = async (fmt: 'csv' | 'json' | 'pdf') => {
    setExportingFmt(fmt)
    try {
      await evaluationService.downloadExport(fmt)
      success('Report Exported', `Downloaded evaluation report (${fmt.toUpperCase()}).`)
    } catch (err: any) {
      toastError('Export Failed', err.message || `Could not export ${fmt.toUpperCase()} report.`)
    } finally {
      setExportingFmt(null)
    }
  }

  const refreshAll = () => {
    summaryQuery.refetch()
    historyQuery.refetch()
  }

  const summary = summaryQuery.data
  const historyItems = historyQuery.data?.items || []
  const isLoading = summaryQuery.isLoading || historyQuery.isLoading

  const latencyBarData = summary
    ? [
        { stage: 'Rewrite', ms: summary.avg_rewrite_latency_ms },
        { stage: 'Planner', ms: summary.avg_planner_latency_ms },
        { stage: 'Retrieval', ms: summary.avg_retrieval_latency_ms },
        { stage: 'Rerank', ms: summary.avg_reranking_latency_ms },
        { stage: 'Generation', ms: summary.avg_generation_latency_ms },
      ]
    : []

  const providerPieData = (summary?.provider_comparison || []).map((p) => ({
    name: p.provider.toUpperCase(),
    value: p.total_runs,
    avgScore: p.avg_overall_score,
  }))

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 pb-14"
    >
      {/* Top Action Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-white/[0.08] gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-cerulean-light mb-1">
            <Gauge className="w-3.5 h-3.5" />
            <span>Sprint 6.0 · RAG Observability & Benchmarking</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Enterprise RAG Evaluation Dashboard
          </h1>
          <p className="text-xs text-jet-400 mt-1">
            Independent observability across retrieval precision, grounding, citation integrity, hallucination risk, and pipeline latency.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="cerulean"
            size="sm"
            onClick={() => benchmarkMutation.mutate()}
            disabled={benchmarkMutation.isPending}
            leftIcon={<Play className="w-3.5 h-3.5" />}
            className="text-xs font-semibold"
          >
            {benchmarkMutation.isPending ? 'Running 55-Query Benchmark...' : 'Run Benchmark (55+)'}
          </Button>

          <Button
            variant="glass"
            size="sm"
            onClick={() => handleExport('csv')}
            disabled={exportingFmt !== null}
            leftIcon={<FileSpreadsheet className="w-3.5 h-3.5" />}
            className="text-xs border-white/10"
          >
            CSV
          </Button>
          <Button
            variant="glass"
            size="sm"
            onClick={() => handleExport('json')}
            disabled={exportingFmt !== null}
            leftIcon={<FileText className="w-3.5 h-3.5" />}
            className="text-xs border-white/10"
          >
            JSON
          </Button>
          <Button
            variant="glass"
            size="sm"
            onClick={() => handleExport('pdf')}
            disabled={exportingFmt !== null}
            leftIcon={<Download className="w-3.5 h-3.5 text-neonrose" />}
            className="text-xs border-white/10"
          >
            PDF
          </Button>

          <Button
            variant="glass"
            size="sm"
            onClick={refreshAll}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
            className="text-xs border-white/10"
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Section 1: Overall Score Strip */}
      <section className="space-y-3">
        <h2 className="text-xs font-mono uppercase tracking-wider text-jet-400">
          Overall RAG Health ({summary?.total_evaluations ?? 0} evaluations)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card variant="cerulean" className="p-4 bg-jet-950/80 border-cerulean/30">
            <span className="text-[11px] font-mono text-jet-400 uppercase">Overall RAG Score</span>
            <div className="mt-2 flex items-baseline space-x-1">
              <span className="text-2xl font-bold text-white">{(summary?.overall_rag_score ?? 0).toFixed(1)}</span>
              <span className="text-xs text-jet-500">/ 100</span>
            </div>
          </Card>

          <Card variant="default" className="p-4 bg-jet-950/80 border-white/[0.08]">
            <span className="text-[11px] font-mono text-jet-400 uppercase">Grounding</span>
            <div className="mt-2 flex items-baseline space-x-1">
              <span className="text-2xl font-bold text-emerald-400">{(summary?.avg_grounding ?? 0).toFixed(1)}%</span>
            </div>
          </Card>

          <Card variant="default" className="p-4 bg-jet-950/80 border-white/[0.08]">
            <span className="text-[11px] font-mono text-jet-400 uppercase">Retrieval Score</span>
            <div className="mt-2 flex items-baseline space-x-1">
              <span className="text-2xl font-bold text-cerulean-light">{(summary?.avg_retrieval_score ?? 0).toFixed(1)}</span>
              <span className="text-xs text-jet-500">/ 100</span>
            </div>
          </Card>

          <Card variant="default" className="p-4 bg-jet-950/80 border-white/[0.08]">
            <span className="text-[11px] font-mono text-jet-400 uppercase">Generation Quality</span>
            <div className="mt-2 flex items-baseline space-x-1">
              <span className="text-2xl font-bold text-white">{(summary?.avg_generation_score ?? 0).toFixed(1)}</span>
              <span className="text-xs text-jet-500">/ 100</span>
            </div>
          </Card>

          <Card variant="default" className="p-4 bg-jet-950/80 border-neonrose/30">
            <span className="text-[11px] font-mono text-jet-400 uppercase">Hallucination Risk</span>
            <div className="mt-2 flex items-baseline space-x-1">
              <span className="text-2xl font-bold text-neonrose">{(summary?.avg_hallucination_risk ?? 0).toFixed(1)}%</span>
              <span className="text-[10px] font-mono text-jet-500">lower is better</span>
            </div>
          </Card>
        </div>
      </section>

      {/* Section 2 & 3: Retrieval Quality & Generation Quality Matrices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Retrieval Quality */}
        <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-cerulean-light" />
              <h3 className="text-sm font-semibold text-white">Retrieval Quality</h3>
            </div>
            <span className="text-[10px] font-mono text-jet-400">RRF (k=60) + Cross-Encoder</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Precision@K</span>
              <span className="text-lg font-bold text-white">{(summary?.avg_precision ?? 0).toFixed(3)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Recall@K</span>
              <span className="text-lg font-bold text-white">{(summary?.avg_recall ?? 0).toFixed(3)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">MRR</span>
              <span className="text-lg font-bold text-cerulean-light">{(summary?.avg_mrr ?? 0).toFixed(3)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">NDCG</span>
              <span className="text-lg font-bold text-cerulean-light">{(summary?.avg_ndcg ?? 0).toFixed(3)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Doc Coverage</span>
              <span className="text-lg font-bold text-emerald-400">{(summary?.avg_retrieval_coverage ?? 0).toFixed(1)}%</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Source Diversity</span>
              <span className="text-lg font-bold text-white">{(summary?.avg_source_diversity ?? 0).toFixed(1)} docs</span>
            </div>
          </div>
        </Card>

        {/* Generation Quality */}
        <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-neonrose" />
              <h3 className="text-sm font-semibold text-white">Generation Quality (0 → 100)</h3>
            </div>
            <span className="text-[10px] font-mono text-jet-400">Non-Destructive Audit</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Grounding</span>
              <span className="text-lg font-bold text-emerald-400">{(summary?.avg_grounding ?? 0).toFixed(1)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Faithfulness</span>
              <span className="text-lg font-bold text-cerulean-light">{(summary?.avg_faithfulness ?? 0).toFixed(1)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Citation Coverage</span>
              <span className="text-lg font-bold text-white">{(summary?.avg_citation_coverage ?? 0).toFixed(1)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Completeness</span>
              <span className="text-lg font-bold text-white">{(summary?.avg_answer_completeness ?? 0).toFixed(1)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Hallucination Risk</span>
              <span className="text-lg font-bold text-neonrose">{(summary?.avg_hallucination_risk ?? 0).toFixed(1)}</span>
            </div>
            <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
              <span className="text-[10px] text-jet-400 block">Reasoning Cov.</span>
              <span className="text-lg font-bold text-white">{(summary?.avg_reasoning_coverage ?? 0).toFixed(1)}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Section 4: Performance & Token Telemetry */}
      <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-cerulean-light" />
            <h3 className="text-sm font-semibold text-white">Pipeline Performance & Token Telemetry</h3>
          </div>
          <span className="text-[10px] font-mono text-jet-400">
            Total Tokens: {(summary?.total_tokens ?? 0).toLocaleString()} ({summary?.avg_tokens_per_query ?? 0}/query)
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
            <span className="text-[10px] text-jet-400 block">Rewrite</span>
            <span className="text-sm font-bold text-white">{(summary?.avg_rewrite_latency_ms ?? 0).toFixed(2)} ms</span>
          </div>
          <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
            <span className="text-[10px] text-jet-400 block">Planner</span>
            <span className="text-sm font-bold text-white">{(summary?.avg_planner_latency_ms ?? 0).toFixed(2)} ms</span>
          </div>
          <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
            <span className="text-[10px] text-jet-400 block">Retrieval</span>
            <span className="text-sm font-bold text-cerulean-light">{(summary?.avg_retrieval_latency_ms ?? 0).toFixed(1)} ms</span>
          </div>
          <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
            <span className="text-[10px] text-jet-400 block">Reranking</span>
            <span className="text-sm font-bold text-neonrose">{(summary?.avg_reranking_latency_ms ?? 0).toFixed(1)} ms</span>
          </div>
          <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
            <span className="text-[10px] text-jet-400 block">Generation</span>
            <span className="text-sm font-bold text-white">{(summary?.avg_generation_latency_ms ?? 0).toFixed(1)} ms</span>
          </div>
          <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
            <span className="text-[10px] text-jet-400 block">Total Avg</span>
            <span className="text-sm font-bold text-emerald-400">{(summary?.avg_total_latency_ms ?? 0).toFixed(1)} ms</span>
          </div>
          <div className="p-3 rounded-xl bg-jet-900/60 border border-white/[0.05]">
            <span className="text-[10px] text-jet-400 block">Avg Tokens</span>
            <span className="text-sm font-bold text-white">{summary?.avg_tokens_per_query ?? 0}</span>
          </div>
        </div>
      </Card>

      {/* Section 5: Recharts Visualization Suite */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Line Chart: Quality Trends */}
        <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-3">
          <h3 className="text-sm font-semibold text-white">Grounding, Faithfulness & Hallucination Trends</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={summary?.trend_series || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="label" stroke="#71717a" fontSize={11} />
                <YAxis stroke="#71717a" fontSize={11} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                <Legend />
                <Line type="monotone" dataKey="grounding" name="Grounding" stroke="#007BA7" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="faithfulness" name="Faithfulness" stroke="#38BDF8" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="hallucination" name="Hallucination Risk" stroke="#FF2D95" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Area Chart: Retrieval Trajectory */}
        <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-3">
          <h3 className="text-sm font-semibold text-white">Retrieval Precision, Recall & NDCG (%)</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={summary?.trend_series || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="label" stroke="#71717a" fontSize={11} />
                <YAxis stroke="#71717a" fontSize={11} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                <Legend />
                <Area type="monotone" dataKey="ndcg" name="NDCG %" stroke="#007BA7" fill="#007BA7" fillOpacity={0.22} />
                <Area type="monotone" dataKey="precision" name="Precision %" stroke="#38BDF8" fill="#38BDF8" fillOpacity={0.15} />
                <Area type="monotone" dataKey="recall" name="Recall %" stroke="#FF2D95" fill="#FF2D95" fillOpacity={0.12} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Bar Chart: Stage Latency Breakdown */}
        <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-3">
          <h3 className="text-sm font-semibold text-white">Pipeline Latency by Stage (ms)</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latencyBarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="stage" stroke="#71717a" fontSize={11} />
                <YAxis stroke="#71717a" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                <Bar dataKey="ms" name="Latency (ms)" radius={[6, 6, 0, 0]}>
                  {latencyBarData.map((_, i) => (
                    <Cell key={i} fill={i === 3 ? '#FF2D95' : '#007BA7'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Pie Chart: Provider Execution Distribution */}
        <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-3">
          <h3 className="text-sm font-semibold text-white">Provider Evaluation Distribution</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={providerPieData.length ? providerPieData : [{ name: 'No Runs', value: 1 }]}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={52}
                  outerRadius={84}
                  paddingAngle={4}
                >
                  {(providerPieData.length ? providerPieData : [{ name: 'No Runs', value: 1 }]).map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Heatmap-Style Quality Matrix */}
      <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Query × Evaluation Quality Matrix (Heatmap)</h3>
          <span className="text-[10px] font-mono text-jet-400">Normalized 0 → 100 across recent queries</span>
        </div>

        {(summary?.heatmap_matrix || []).length === 0 ? (
          <p className="text-xs text-jet-400 py-4">Send a chat query or run the benchmark suite to populate the evaluation heatmap.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono border-collapse">
              <thead>
                <tr className="text-jet-400 border-b border-white/[0.08]">
                  <th className="text-left py-2 pr-3">Query</th>
                  <th className="py-2 px-2 text-center">Precision</th>
                  <th className="py-2 px-2 text-center">Recall</th>
                  <th className="py-2 px-2 text-center">NDCG</th>
                  <th className="py-2 px-2 text-center">Grounding</th>
                  <th className="py-2 px-2 text-center">Faithfulness</th>
                  <th className="py-2 px-2 text-center">Citation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {(summary?.heatmap_matrix || []).map((row, idx) => (
                  <tr key={idx}>
                    <td className="py-2 pr-3 text-jet-200 font-sans truncate max-w-[220px]">{row.query}</td>
                    {(['Precision', 'Recall', 'NDCG', 'Grounding', 'Faithfulness', 'Citation'] as const).map((col) => (
                      <td key={col} className="p-1 text-center">
                        <span className={`inline-block w-full py-1 rounded border text-[11px] ${getHeatmapColor(row[col])}`}>
                          {row[col].toFixed(0)}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Section 6: Evaluation History Table (Last 100 with Expandable Rows) */}
      <Card className="p-5 bg-jet-950/80 border-white/[0.08] space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-cerulean-light" />
            <h3 className="text-sm font-semibold text-white">Evaluation History (Last 100)</h3>
          </div>
          <span className="text-[11px] font-mono text-jet-400">Click any row to inspect full report</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="text-[11px] font-mono uppercase text-jet-400 border-b border-white/[0.08]">
                <th className="py-2.5 px-2 text-left"></th>
                <th className="py-2.5 px-2 text-left">Timestamp</th>
                <th className="py-2.5 px-2 text-left">Query</th>
                <th className="py-2.5 px-2 text-left">Provider</th>
                <th className="py-2.5 px-2 text-left">Model</th>
                <th className="py-2.5 px-2 text-right">Confidence</th>
                <th className="py-2.5 px-2 text-right">Precision</th>
                <th className="py-2.5 px-2 text-right">Recall</th>
                <th className="py-2.5 px-2 text-right">MRR</th>
                <th className="py-2.5 px-2 text-right">Grounding</th>
                <th className="py-2.5 px-2 text-right">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.05]">
              {historyItems.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-jet-400">
                    No evaluations persisted yet. Ask a question in Chat Studio or click Run Benchmark.
                  </td>
                </tr>
              ) : (
                historyItems.map((rec: EvaluationRecord) => {
                  const isExpanded = expandedRowId === rec.id
                  return (
                    <React.Fragment key={rec.id}>
                      <tr
                        onClick={() => setExpandedRowId(isExpanded ? null : rec.id)}
                        className="hover:bg-white/[0.03] cursor-pointer transition-colors"
                      >
                        <td className="py-2.5 px-2 text-jet-400">
                          {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                        </td>
                        <td className="py-2.5 px-2 font-mono text-[11px] text-jet-400 whitespace-nowrap">
                          {new Date(rec.created_at).toLocaleString()}
                        </td>
                        <td className="py-2.5 px-2 text-white max-w-[260px] truncate">{rec.query}</td>
                        <td className="py-2.5 px-2 font-mono text-cerulean-light uppercase">{rec.provider}</td>
                        <td className="py-2.5 px-2 font-mono text-jet-300 truncate max-w-[140px]">{rec.model}</td>
                        <td className="py-2.5 px-2 font-mono text-right text-jet-200">{rec.confidence.toFixed(1)}%</td>
                        <td className="py-2.5 px-2 font-mono text-right text-white">{rec.retrieval.precision_at_k.toFixed(2)}</td>
                        <td className="py-2.5 px-2 font-mono text-right text-white">{rec.retrieval.recall_at_k.toFixed(2)}</td>
                        <td className="py-2.5 px-2 font-mono text-right text-cerulean-light">{rec.retrieval.mrr.toFixed(2)}</td>
                        <td className="py-2.5 px-2 font-mono text-right text-emerald-400">{rec.generation.grounding_score.toFixed(1)}%</td>
                        <td className="py-2.5 px-2 font-mono text-right text-jet-300">{rec.performance.total_response_time_ms.toFixed(0)}ms</td>
                      </tr>

                      {isExpanded && (
                        <tr className="bg-jet-900/50">
                          <td colSpan={11} className="p-4">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                              {/* Retrieval Breakdown */}
                              <div className="p-3 rounded-xl bg-jet-950/80 border border-white/[0.06] space-y-1.5 font-mono">
                                <div className="text-[10px] uppercase text-cerulean-light font-semibold">Retrieval Report</div>
                                <div className="flex justify-between"><span className="text-jet-400">DCG / IDCG / NDCG:</span><span>{rec.retrieval.dcg} / {rec.retrieval.idcg} / {rec.retrieval.ndcg}</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Context Recall:</span><span>{rec.retrieval.context_recall}%</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Doc Coverage:</span><span>{rec.retrieval.retrieval_coverage}%</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Source Diversity:</span><span>{rec.retrieval.source_diversity} files</span></div>
                              </div>

                              {/* Generation & Citations */}
                              <div className="p-3 rounded-xl bg-jet-950/80 border border-white/[0.06] space-y-1.5 font-mono">
                                <div className="text-[10px] uppercase text-neonrose font-semibold">Generation & Citations</div>
                                <div className="flex justify-between"><span className="text-jet-400">Faithfulness / Completeness:</span><span>{rec.generation.faithfulness} / {rec.generation.answer_completeness}</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Hallucination Risk:</span><span className="text-neonrose">{rec.generation.hallucination_risk}%</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Citations Valid:</span><span>{rec.citation_verification.valid_citations}/{rec.citation_verification.total_citations} ({rec.citation_verification.citation_score}%)</span></div>
                                {rec.citation_verification.warnings.length > 0 ? (
                                  <div className="text-[11px] text-amber-300 flex items-start gap-1 pt-1">
                                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                                    <span>{rec.citation_verification.warnings[0]}</span>
                                  </div>
                                ) : (
                                  <div className="text-[11px] text-emerald-400 flex items-center gap-1 pt-1">
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                    <span>Citation integrity verified</span>
                                  </div>
                                )}
                              </div>

                              {/* Performance & Tokens */}
                              <div className="p-3 rounded-xl bg-jet-950/80 border border-white/[0.06] space-y-1.5 font-mono">
                                <div className="text-[10px] uppercase text-emerald-400 font-semibold">Latencies & Tokens</div>
                                <div className="flex justify-between"><span className="text-jet-400">Rewrite / Planner:</span><span>{rec.performance.query_rewrite_latency_ms}ms / {rec.performance.planner_latency_ms}ms</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Retrieval / Rerank:</span><span>{rec.performance.retrieval_latency_ms}ms / {rec.performance.reranking_latency_ms}ms</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Eval Overhead:</span><span className="text-emerald-400">{rec.performance.evaluation_latency_ms}ms</span></div>
                                <div className="flex justify-between"><span className="text-jet-400">Tokens (P/C/T):</span><span>{rec.performance.prompt_tokens}/{rec.performance.completion_tokens}/{rec.performance.total_tokens}</span></div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  )
}

export default EvaluationPage


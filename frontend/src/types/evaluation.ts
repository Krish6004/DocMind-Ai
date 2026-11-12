export interface CitationCheckItem {
  citation_num: number
  citation_exists: boolean
  chunk_exists: boolean
  filename?: string | null
  page_number?: number | string | null
  chunk_index?: number | string | null
  chunk_text_matches: boolean
  warning?: string | null
}

export interface CitationVerificationResult {
  total_citations: number
  valid_citations: number
  citation_score: number
  items: CitationCheckItem[]
  warnings: string[]
}

export interface RetrievalMetricsDetail {
  precision_at_k: number
  recall_at_k: number
  mrr: number
  dcg: number
  idcg: number
  ndcg: number
  context_recall: number
  retrieval_coverage: number
  source_diversity: number
}

export interface GenerationMetricsDetail {
  grounding_score: number
  faithfulness: number
  citation_coverage: number
  context_utilization: number
  answer_completeness: number
  hallucination_risk: number
  source_utilization: number
  answer_length: number
  reasoning_coverage: number
}

export interface PerformanceMetricsDetail {
  query_rewrite_latency_ms: number
  planner_latency_ms: number
  retrieval_latency_ms: number
  reranking_latency_ms: number
  generation_latency_ms: number
  confidence_latency_ms: number
  memory_retrieval_time_ms: number
  evaluation_latency_ms: number
  total_response_time_ms: number
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  retrieved_chunk_count: number
  reranked_chunk_count: number
  document_count: number
  provider: string
  model: string
}

export interface EvaluationRecord {
  id: string
  request_id: string
  session_id: string
  query: string
  answer?: string | null
  provider: string
  model: string
  confidence: number
  overall_score: number
  retrieval: RetrievalMetricsDetail
  generation: GenerationMetricsDetail
  citation_verification: CitationVerificationResult
  performance: PerformanceMetricsDetail
  is_benchmark: boolean
  created_at: string
}

export interface EvaluationHistoryListResponse {
  total: number
  items: EvaluationRecord[]
}

export interface ProviderComparisonEntry {
  provider: string
  total_runs: number
  avg_overall_score: number
  avg_grounding: number
  avg_faithfulness: number
  avg_hallucination_risk: number
  avg_latency_ms: number
  avg_tokens: number
}

export interface EvaluationSummaryResponse {
  total_evaluations: number
  overall_rag_score: number
  avg_grounding: number
  avg_retrieval_score: number
  avg_generation_score: number
  avg_hallucination_risk: number
  avg_precision: number
  avg_recall: number
  avg_mrr: number
  avg_ndcg: number
  avg_context_recall: number
  avg_retrieval_coverage: number
  avg_source_diversity: number
  avg_faithfulness: number
  avg_citation_coverage: number
  avg_context_utilization: number
  avg_answer_completeness: number
  avg_source_utilization: number
  avg_reasoning_coverage: number
  avg_confidence: number
  avg_total_latency_ms: number
  avg_rewrite_latency_ms: number
  avg_planner_latency_ms: number
  avg_retrieval_latency_ms: number
  avg_reranking_latency_ms: number
  avg_generation_latency_ms: number
  total_tokens: number
  avg_tokens_per_query: number
  provider_comparison: ProviderComparisonEntry[]
  trend_series: Array<{
    index: number
    label: string
    query: string
    overall_score: number
    grounding: number
    faithfulness: number
    hallucination: number
    precision: number
    recall: number
    ndcg: number
    latency_ms: number
    tokens: number
  }>
  heatmap_matrix: Array<{
    query: string
    Precision: number
    Recall: number
    NDCG: number
    Grounding: number
    Faithfulness: number
    Citation: number
  }>
}

export interface BenchmarkRunRequest {
  dataset_name?: string
  max_queries?: number
  use_live_llm?: boolean
}

export interface BenchmarkRunResponse {
  run_id: string
  dataset_name: string
  total_queries: number
  avg_precision: number
  avg_recall: number
  avg_mrr: number
  avg_ndcg: number
  avg_grounding: number
  avg_faithfulness: number
  avg_hallucination: number
  avg_latency_ms: number
  avg_confidence: number
  document_coverage: number
  provider_comparison: ProviderComparisonEntry[]
  executed_at: string
  sample_results: EvaluationRecord[]
}


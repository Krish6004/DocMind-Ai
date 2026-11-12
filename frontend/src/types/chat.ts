/**
 * Chat and RAG query contracts matching POST /api/v1/chat and history schemas.
 */

export interface SourceChunk {
  source_num: number
  filename: string
  chunk_index: number | string
  score: number
  text?: string | null
  metadata?: Record<string, any> | null
}

export interface ConfidenceDetails {
  score: number
  percentage: number
  level: 'High' | 'Medium' | 'Low' | string
  color: string
  explanation: string
  details?: Record<string, any> | null
}

export interface LatencyMetrics {
  retrieval_latency_ms: number
  reranking_latency_ms: number
  generation_latency_ms: number
  total_latency_ms: number
  retrieved_chunk_count: number
  reranked_chunk_count: number
  rewrite_latency_ms?: number
  planner_latency_ms?: number
}

export interface QueryRewriteTelemetry {
  original_query: string
  rewritten_query: string
  rewrite_time_ms: number
  status: 'rewritten' | 'skipped' | 'disabled' | 'failed' | string
  is_rewritten: boolean
}

export interface RetrievalPlannerTelemetry {
  query_type: string
  strategy_name: string
  recommended_top_k: number
  recommended_rerank_count: number
  needs_memory: boolean
  needs_metadata_filter: boolean
  reason: string
  decision_time_ms: number
}

export interface ChatRequest {
  query: string
  session_id?: string | null
  top_k?: number
  filters?: Record<string, any> | null
  use_memory?: boolean
  memory_window?: number
}

export interface ChatResponseData {
  request_id: string
  session_id: string
  query: string
  answer: string
  sources: SourceChunk[]
  confidence: ConfidenceDetails
  metrics: LatencyMetrics
  query_rewrite?: QueryRewriteTelemetry | null
  retrieval_planner?: RetrievalPlannerTelemetry | null
  model: string
  created_at: string
}

export interface ChatHistoryTurn {
  id: string
  session_id: string
  query: string
  answer: string
  sources?: SourceChunk[] | Record<string, any>[] | null
  confidence_score?: number | null
  latency_ms?: number | null
  created_at: string
}

export interface ChatHistoryResponse {
  session_id: string
  total_turns: number
  history: ChatHistoryTurn[]
}

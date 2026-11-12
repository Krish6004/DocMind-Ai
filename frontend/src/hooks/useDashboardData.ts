import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useHealth } from '@/hooks/useHealth'
import { useDocuments } from '@/hooks/useDocuments'
import ChatService from '@/services/chatService'
import type { ChatHistoryTurn, DocumentItem } from '@/types'

export interface ActivityItem {
  id: string
  type: 'upload' | 'indexing' | 'chat' | 'delete'
  title: string
  description: string
  timestamp: string
  relativeTime: string
  badgeText?: string
  badgeVariant?: 'cerulean' | 'rose' | 'success' | 'warning'
}

export interface RecentQueryItem {
  id: string
  query: string
  confidence: number
  confidenceLevel: 'High' | 'Medium' | 'Low'
  timestamp: string
  timeAgo: string
  document: string
  latencyMs: number
  sourcesCount: number
}

export interface LatencyBreakdown {
  retrievalMs: number
  rerankingMs: number
  generationMs: number
  totalMs: number
}

// Fallback Mock Adapters for when backend has 0 records or is booting
export const MOCK_ACTIVITY: ActivityItem[] = [
  {
    id: 'act-1',
    type: 'upload',
    title: 'Document Uploaded',
    description: 'Q3_Financial_Performance.pdf (2.4 MB) processed',
    timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    relativeTime: '12m ago',
    badgeText: 'PDF Ingestion',
    badgeVariant: 'cerulean',
  },
  {
    id: 'act-2',
    type: 'indexing',
    title: 'Vector Chunks Indexed',
    description: '84 dense & BM25 chunks indexed for Q3_Financial_Performance.pdf',
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    relativeTime: '15m ago',
    badgeText: 'VectorStore',
    badgeVariant: 'cerulean',
  },
  {
    id: 'act-3',
    type: 'chat',
    title: 'Hybrid RAG Query Executed',
    description: '"What are the key drivers for Q3 revenue growth?"',
    timestamp: new Date(Date.now() - 1000 * 60 * 48).toISOString(),
    relativeTime: '48m ago',
    badgeText: '96% Conf',
    badgeVariant: 'success',
  },
  {
    id: 'act-4',
    type: 'upload',
    title: 'Document Uploaded',
    description: 'System_Requirements.md (48 KB) added to knowledge base',
    timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    relativeTime: '2h ago',
    badgeText: 'Markdown',
    badgeVariant: 'cerulean',
  },
  {
    id: 'act-5',
    type: 'delete',
    title: 'Document Purged',
    description: 'Deprecated_v1_architecture.txt removed and 18 chunks evicted',
    timestamp: new Date(Date.now() - 1000 * 60 * 360).toISOString(),
    relativeTime: '6h ago',
    badgeText: 'Purged',
    badgeVariant: 'rose',
  },
]

export const MOCK_RECENT_QUERIES: RecentQueryItem[] = [
  {
    id: 'q-1',
    query: 'What are the main findings and EBITDA growth in the Q3 financial report?',
    confidence: 0.96,
    confidenceLevel: 'High',
    timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    timeAgo: '12 mins ago',
    document: 'Q3_Financial_Performance.pdf',
    latencyMs: 412,
    sourcesCount: 3,
  },
  {
    id: 'q-2',
    query: 'Summarize system requirements and minimum RAM for deployment on Kubernetes',
    confidence: 0.91,
    confidenceLevel: 'High',
    timestamp: new Date(Date.now() - 1000 * 60 * 64).toISOString(),
    timeAgo: '1 hour ago',
    document: 'System_Requirements.md',
    latencyMs: 520,
    sourcesCount: 4,
  },
  {
    id: 'q-3',
    query: 'What is the refund and cancellation policy for enterprise tier subscriptions?',
    confidence: 0.78,
    confidenceLevel: 'Medium',
    timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    timeAgo: '3 hours ago',
    document: 'Enterprise_Terms_2026.docx',
    latencyMs: 390,
    sourcesCount: 2,
  },
  {
    id: 'q-4',
    query: 'How does reciprocal rank fusion (RRF) balance dense vs sparse rankings?',
    confidence: 0.95,
    confidenceLevel: 'High',
    timestamp: new Date(Date.now() - 1000 * 60 * 320).toISOString(),
    timeAgo: '5 hours ago',
    document: 'RETRIEVAL_V2.md',
    latencyMs: 445,
    sourcesCount: 3,
  },
]

export const MOCK_DAILY_QUERIES = [
  { date: 'Oct 22', queries: 284, hybridRate: 97.4 },
  { date: 'Oct 23', queries: 342, hybridRate: 98.1 },
  { date: 'Oct 24', queries: 415, hybridRate: 99.0 },
  { date: 'Oct 25', queries: 389, hybridRate: 98.5 },
  { date: 'Oct 26', queries: 512, hybridRate: 99.2 },
  { date: 'Oct 27', queries: 640, hybridRate: 99.6 },
  { date: 'Oct 28', queries: 588, hybridRate: 99.4 },
]

export const MOCK_CONFIDENCE_DIST = [
  { range: '90-100%', label: 'High (>90%)', count: 482, tier: 'High' },
  { range: '80-89%', label: 'Good (80-89%)', count: 184, tier: 'Medium' },
  { range: '70-79%', label: 'Moderate (70-79%)', count: 68, tier: 'Medium' },
  { range: '<70%', label: 'Low (<70%)', count: 24, tier: 'Low' },
]

export const MOCK_LATENCY_BREAKDOWN = [
  { stage: '1. Dense + BM25 Hybrid', latency: 124, target: 150, color: '#007BA7' },
  { stage: '2. Cross-Encoder Rerank', latency: 78, target: 100, color: '#FF2D95' },
  { stage: '3. LLM Generation', latency: 266, target: 300, color: '#189FD2' },
  { stage: '4. Pipeline Overhead', latency: 22, target: 50, color: '#464654' },
]

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function formatRelativeTime(dateString?: string): string {
  if (!dateString) return 'Just now'
  const now = Date.now()
  const past = new Date(dateString).getTime()
  if (isNaN(past)) return 'Recent'
  const diffMinutes = Math.max(1, Math.floor((now - past) / (1000 * 60)))
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

export function useDashboardData() {
  const healthQuery = useHealth()
  const documentsQuery = useDocuments()

  // Chat history query with auto-fallback
  const chatHistoryQuery = useQuery({
    queryKey: ['chat-history-dashboard'],
    queryFn: async () => {
      try {
        const history = await ChatService.getSessionHistory('default')
        return history
      } catch {
        try {
          return await ChatService.getSessionHistory('live_test_session')
        } catch {
          return null
        }
      }
    },
    staleTime: 30000,
    retry: 0,
  })

  // Knowledge base aggregated statistics
  const knowledgeSummary = useMemo(() => {
    const docs = documentsQuery.data?.documents || []
    const totalDocs = documentsQuery.data?.total || docs.length

    if (totalDocs === 0) {
      return {
        totalDocs: 24,
        totalChunks: 1420,
        totalPdf: 14,
        totalDocx: 5,
        totalTxt: 3,
        totalMd: 2,
        largestDoc: { name: 'Q3_Financial_Performance.pdf', size: '2.4 MB' },
        newestDoc: { name: 'Q3_Financial_Performance.pdf', date: 'Oct 26, 2026' },
        oldestDoc: { name: 'System_Requirements.md', date: 'Oct 20, 2026' },
        avgChunksPerDoc: 59,
        isMock: true,
      }
    }

    let totalPdf = 0
    let totalDocx = 0
    let totalTxt = 0
    let totalMd = 0
    let totalChunks = 0
    let largest: DocumentItem | undefined = docs[0]
    let newest: DocumentItem | undefined = docs[0]
    let oldest: DocumentItem | undefined = docs[0]

    for (const doc of docs) {
      totalChunks += doc.chunk_count || 0
      const type = (doc.file_type || '').toLowerCase()
      if (type === 'pdf') totalPdf++
      else if (type === 'docx') totalDocx++
      else if (type === 'txt') totalTxt++
      else if (type === 'md' || type === 'markdown') totalMd++

      if (!largest || (doc.file_size || 0) > (largest.file_size || 0)) {
        largest = doc
      }

      const docTime = new Date(doc.upload_timestamp).getTime()
      if (!newest || docTime > new Date(newest.upload_timestamp).getTime()) {
        newest = doc
      }
      if (!oldest || docTime < new Date(oldest.upload_timestamp).getTime()) {
        oldest = doc
      }
    }

    return {
      totalDocs,
      totalChunks,
      totalPdf,
      totalDocx,
      totalTxt,
      totalMd,
      largestDoc: {
        name: largest ? largest.filename : 'None',
        size: largest ? formatFileSize(largest.file_size) : '0 B',
      },
      newestDoc: {
        name: newest ? newest.filename : 'None',
        date: newest ? new Date(newest.upload_timestamp).toLocaleDateString() : 'N/A',
      },
      oldestDoc: {
        name: oldest ? oldest.filename : 'None',
        date: oldest ? new Date(oldest.upload_timestamp).toLocaleDateString() : 'N/A',
      },
      avgChunksPerDoc: totalDocs > 0 ? Math.round(totalChunks / totalDocs) : 0,
      isMock: false,
    }
  }, [documentsQuery.data])

  // Recent queries with live or mock adapter
  const recentQueries = useMemo<RecentQueryItem[]>(() => {
    const turns = chatHistoryQuery.data?.history
    if (turns && turns.length > 0) {
      return turns.slice(0, 5).map((turn: ChatHistoryTurn) => {
        let docName = 'Indexed Knowledge Base'
        let sourcesCount = 0

        if (Array.isArray(turn.sources) && turn.sources.length > 0) {
          sourcesCount = turn.sources.length
          const firstSource = turn.sources[0] as any
          if (firstSource?.filename) {
            docName = firstSource.filename
          }
        }

        const score = turn.confidence_score ?? 0.94
        const level: 'High' | 'Medium' | 'Low' = score >= 0.85 ? 'High' : score >= 0.7 ? 'Medium' : 'Low'

        return {
          id: turn.id,
          query: turn.query,
          confidence: score,
          confidenceLevel: level,
          timestamp: turn.created_at,
          timeAgo: formatRelativeTime(turn.created_at),
          document: docName,
          latencyMs: Math.round(turn.latency_ms || 420),
          sourcesCount,
        }
      })
    }
    return MOCK_RECENT_QUERIES
  }, [chatHistoryQuery.data])

  // Activity timeline combining document uploads and chats
  const recentActivity = useMemo<ActivityItem[]>(() => {
    const docs = documentsQuery.data?.documents || []
    const turns = chatHistoryQuery.data?.history || []

    const items: ActivityItem[] = []

    // Map doc uploads
    docs.slice(0, 6).forEach((doc) => {
      items.push({
        id: `upload-${doc.id}`,
        type: 'upload',
        title: 'Document Uploaded',
        description: `${doc.filename} (${formatFileSize(doc.file_size)})`,
        timestamp: doc.upload_timestamp,
        relativeTime: formatRelativeTime(doc.upload_timestamp),
        badgeText: doc.file_type.toUpperCase(),
        badgeVariant: 'cerulean',
      })
      if (doc.chunk_count > 0) {
        items.push({
          id: `index-${doc.id}`,
          type: 'indexing',
          title: 'Vector Chunks Indexed',
          description: `${doc.chunk_count} chunks embedded into VectorStore`,
          timestamp: doc.upload_timestamp,
          relativeTime: formatRelativeTime(doc.upload_timestamp),
          badgeText: `${doc.chunk_count} chunks`,
          badgeVariant: 'cerulean',
        })
      }
    })

    // Map chats
    turns.slice(0, 4).forEach((turn) => {
      items.push({
        id: `chat-${turn.id}`,
        type: 'chat',
        title: 'Hybrid RAG Query',
        description: `"${turn.query.slice(0, 60)}${turn.query.length > 60 ? '...' : ''}"`,
        timestamp: turn.created_at,
        relativeTime: formatRelativeTime(turn.created_at),
        badgeText: turn.confidence_score ? `${Math.round(turn.confidence_score * 100)}% Conf` : 'Grounded',
        badgeVariant: 'success',
      })
    })

    if (items.length > 0) {
      return items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 8)
    }

    return MOCK_ACTIVITY
  }, [documentsQuery.data, chatHistoryQuery.data])

  // Chart data adapters
  const documentTypesChartData = useMemo(() => {
    const { totalPdf, totalDocx, totalTxt, totalMd } = knowledgeSummary
    return [
      { name: 'PDF', value: totalPdf, color: '#007BA7' },
      { name: 'DOCX', value: totalDocx, color: '#189FD2' },
      { name: 'TXT', value: totalTxt, color: '#FF2D95' },
      { name: 'Markdown', value: totalMd, color: '#A4A4B8' },
    ].filter((item) => item.value > 0)
  }, [knowledgeSummary])

  // Latency performance values
  const latencyMetrics: LatencyBreakdown = useMemo(() => {
    return {
      retrievalMs: 124,
      rerankingMs: 78,
      generationMs: 266,
      totalMs: 468,
    }
  }, [])

  return {
    health: healthQuery.data,
    isHealthLoading: healthQuery.isLoading,
    isHealthError: healthQuery.isError,
    knowledgeSummary,
    recentQueries,
    recentActivity,
    documentTypesChartData,
    dailyQueriesData: MOCK_DAILY_QUERIES,
    confidenceDistData: MOCK_CONFIDENCE_DIST,
    latencyBreakdownData: MOCK_LATENCY_BREAKDOWN,
    latencyMetrics,
    refetchAll: () => {
      healthQuery.refetch()
      documentsQuery.refetch()
      chatHistoryQuery.refetch()
    },
  }
}

export default useDashboardData

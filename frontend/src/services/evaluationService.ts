import apiClient from './apiClient'
import type {
  ApiResponse,
  BenchmarkRunRequest,
  BenchmarkRunResponse,
  EvaluationHistoryListResponse,
  EvaluationRecord,
  EvaluationSummaryResponse,
} from '@/types'

export const evaluationService = {
  async getLatest(): Promise<EvaluationRecord | null> {
    const res = await apiClient.get<ApiResponse<EvaluationRecord | null>>('/evaluation/latest')
    return res.data.data
  },

  async getHistory(limit = 100, offset = 0): Promise<EvaluationHistoryListResponse> {
    const res = await apiClient.get<ApiResponse<EvaluationHistoryListResponse>>('/evaluation/history', {
      params: { limit, offset },
    })
    return res.data.data
  },

  async getSummary(): Promise<EvaluationSummaryResponse> {
    const res = await apiClient.get<ApiResponse<EvaluationSummaryResponse>>('/evaluation/summary')
    return res.data.data
  },

  async runBenchmark(payload: BenchmarkRunRequest = {}): Promise<BenchmarkRunResponse> {
    const res = await apiClient.post<ApiResponse<BenchmarkRunResponse>>('/evaluation/run', payload, {
      timeout: 120000,
    })
    return res.data.data
  },

  async downloadExport(format: 'csv' | 'json' | 'pdf'): Promise<void> {
    const response = await apiClient.get('/evaluation/export', {
      params: { format },
      responseType: 'blob',
    })
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `docmind_evaluation_report.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

export default evaluationService

import apiClient from './apiClient'
import type { 
  ChatRequest, 
  ChatResponseData, 
  ChatHistoryResponse, 
  ApiResponse 
} from '@/types'

export class ChatService {
  /**
   * Execute Hybrid Retrieval + Reranking + LLM Generation query.
   */
  public static async sendMessage(payload: ChatRequest): Promise<ChatResponseData> {
    const response = await apiClient.post<ApiResponse<ChatResponseData>>('/chat', payload)
    return response.data.data
  }

  /**
   * Fetch conversation history for a given session.
   */
  public static async getSessionHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const response = await apiClient.get<ApiResponse<ChatHistoryResponse>>(`/chat/history/${sessionId}`)
    return response.data.data
  }
}

export default ChatService

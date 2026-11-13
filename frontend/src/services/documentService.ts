import apiClient from './apiClient'
import type { 
  DocumentListResponse, 
  DocumentItem, 
  DocumentUploadResponse, 
  DocumentDeleteResponse,
  ApiResponse 
} from '@/types'

export class DocumentService {
  /**
   * Fetch list of all indexed documents in SQLite metadata repository.
   */
  public static async getDocuments(): Promise<DocumentListResponse> {
    const response = await apiClient.get<ApiResponse<DocumentListResponse>>('/documents')
    return response.data.data
  }

  /**
   * Upload and ingest single/multiple files into RAG pipeline.
   * Configured with a 300s (5-minute) timeout to allow heavy PDF parsing,
   * chunking, neural model downloads, and vector embedding computations.
   */
  public static async uploadDocument(
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<ApiResponse<DocumentUploadResponse>>('/upload', formData, {
      timeout: 300000, // 5 minutes timeout for document upload and RAG indexing
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
    })
    return response.data.data
  }

  /**
   * Delete document by UUID and purge associated vector chunks.
   */
  public static async deleteDocument(id: string): Promise<DocumentDeleteResponse> {
    const response = await apiClient.delete<ApiResponse<DocumentDeleteResponse>>(`/documents/${id}`)
    return response.data.data
  }
}

export default DocumentService

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
   */
  public static async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<ApiResponse<DocumentUploadResponse>>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
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

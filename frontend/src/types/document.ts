/**
 * Document schemas matching GET /api/v1/documents, POST /api/v1/upload, and DELETE /api/v1/documents/{id}.
 */

export interface DocumentItem {
  id: string
  filename: string
  file_type: 'pdf' | 'docx' | 'txt' | 'md' | string
  file_size: number
  page_count: number | null
  chunk_count: number
  status: 'indexed' | 'indexing' | 'failed' | string
  upload_timestamp: string
  file_path?: string | null
}

export interface DocumentListResponse {
  total: number
  documents: DocumentItem[]
}

export interface DocumentUploadResponse {
  id: string
  filename: string
  file_type: string
  file_size: number
  page_count: number | null
  chunk_count: number
  status: string
  upload_timestamp: string
  message: string
}

export interface DocumentDeleteResponse {
  id: string
  filename: string
  removed_chunks: number
  message: string
}

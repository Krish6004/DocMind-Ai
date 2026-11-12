import { useQuery } from '@tanstack/react-query'
import DocumentService from '@/services/documentService'
import type { DocumentListResponse } from '@/types'

export const DOCUMENTS_QUERY_KEY = ['documents-list']

export const useDocuments = () => {
  return useQuery<DocumentListResponse, Error>({
    queryKey: DOCUMENTS_QUERY_KEY,
    queryFn: async () => {
      return await DocumentService.getDocuments()
    },
    refetchInterval: 20000, // Poll every 20 seconds
    staleTime: 15000,
    retry: 1,
  })
}

export default useDocuments


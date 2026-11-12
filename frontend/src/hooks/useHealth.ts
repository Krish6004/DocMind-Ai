import { useQuery } from '@tanstack/react-query'
import HealthService from '@/services/healthService'
import type { HealthResponse } from '@/types'

export const HEALTH_QUERY_KEY = ['backend-health']

export const useHealth = () => {
  return useQuery<HealthResponse, Error>({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: async () => {
      return await HealthService.getHealth()
    },
    refetchInterval: 15000, // Poll every 15 seconds
    staleTime: 10000,
    retry: 2,
  })
}

export default useHealth

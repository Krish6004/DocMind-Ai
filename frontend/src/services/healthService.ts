import apiClient from './apiClient'
import type { HealthResponse } from '@/types'

export class HealthService {
  /**
   * Fetch current backend operational health status.
   */
  public static async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health')
    return response.data
  }
}

export default HealthService

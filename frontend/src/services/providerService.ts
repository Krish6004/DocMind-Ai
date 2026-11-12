import apiClient from './apiClient'
import type {
  ApiResponse,
  ProviderInfo,
  ProviderListResponse,
  ProviderPriorityUpdateRequest,
  ProviderTestRequest,
  ProviderTestResponse,
  ProviderUpdateRequest,
} from '@/types'

export const providerService = {
  /**
   * Fetch all configured AI providers, active provider, and priority list.
   */
  async getProviders(): Promise<ProviderListResponse> {
    const response = await apiClient.get<ApiResponse<ProviderListResponse>>('/providers')
    return response.data.data
  },

  /**
   * Fetch a single provider's details.
   */
  async getProvider(providerId: string): Promise<ProviderInfo> {
    const response = await apiClient.get<ApiResponse<ProviderInfo>>(`/providers/${providerId}`)
    return response.data.data
  },

  /**
   * Test connection and latency for a provider.
   */
  async testProvider(
    providerId: string,
    payload?: ProviderTestRequest
  ): Promise<ProviderTestResponse> {
    const response = await apiClient.post<ApiResponse<ProviderTestResponse>>(
      `/providers/${providerId}/test`,
      payload || {}
    )
    return response.data.data
  },

  /**
   * Update provider settings, mode (developer vs byok), model, or credentials.
   */
  async updateProvider(
    providerId: string,
    payload: ProviderUpdateRequest
  ): Promise<ProviderInfo> {
    const response = await apiClient.put<ApiResponse<ProviderInfo>>(
      `/providers/${providerId}`,
      payload
    )
    return response.data.data
  },

  /**
   * Reorder provider fallback priority.
   */
  async updatePriorityOrder(payload: ProviderPriorityUpdateRequest): Promise<string[]> {
    const response = await apiClient.put<ApiResponse<string[]>>(
      '/providers/priority/order',
      payload
    )
    return response.data.data
  },

  /**
   * Quick-select a provider as the primary active generator.
   */
  async setActiveProvider(providerId: string): Promise<string> {
    const response = await apiClient.post<ApiResponse<string>>(
      `/providers/active/${providerId}`
    )
    return response.data.data
  },
}

export default providerService

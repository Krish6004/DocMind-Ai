export type ProviderID = 'gemini' | 'groq' | 'openai' | 'anthropic' | 'ollama' | string
export type ProviderMode = 'developer' | 'byok'
export type ProviderStatus = 'Connected' | 'Not Configured' | 'Coming Soon' | 'Failed' | 'connected' | 'not_connected' | 'error' | 'untested'

export interface ProviderInfo {
  id: ProviderID
  name: string
  tagline: string
  description: string
  credential_source: string
  status: string
  has_api_key: boolean
  active_model: string
  selected_model: string
  supported_models: string[]
  is_default: boolean
  is_fallback: boolean
  is_coming_soon: boolean
  is_active: boolean
  priority_order: number
  last_latency_ms: number | null
  last_tested_at: string | null
  mode?: ProviderMode
  key_source?: 'env' | 'byok' | 'none'
  masked_key?: string | null
  base_url?: string
  is_enabled?: boolean
}

export interface ProviderListResponse {
  active_provider: string
  fallback_provider?: string
  priority_order: string[]
  providers: ProviderInfo[]
}

export interface ProviderTestRequest {
  api_key?: string
  base_url?: string
  model?: string
}

export interface ProviderTestResponse {
  provider_id: string
  status: string
  latency_ms: number | null
  model: string
  message: string
  error_message: string | null
}

export interface ProviderUpdateRequest {
  mode?: ProviderMode
  api_key?: string
  base_url?: string
  selected_model?: string
  is_enabled?: boolean
  is_active?: boolean
}

export interface ProviderPriorityUpdateRequest {
  priority_order: string[]
  active_provider?: string
}

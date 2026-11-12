export interface AuthUser {
  id: string
  name: string
  email: string
  avatar_url?: string | null
  is_active: boolean
  created_at: string
  last_login?: string | null
}

export interface AuthTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

export interface UserSettings {
  preferred_provider: string
  preferred_model: string
  theme: string
  temperature: number
  top_k: number
  memory_enabled: boolean
}

export interface MongoChatSession {
  conversation_id: string
  user_id: string
  title: string
  last_message: string
  is_pinned: boolean
  message_count: number
  created_at: string
  updated_at: string
  messages?: any[]
}

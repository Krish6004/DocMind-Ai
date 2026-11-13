import apiClient, { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, AUTH_BASE_URL } from './apiClient'
import type {
  ApiResponse,
  AuthTokenResponse,
  AuthUser,
  MongoChatSession,
  UserSettings,
} from '@/types'

export const authService = {
  async register(name: string, email: string, password: string): Promise<AuthTokenResponse> {
    const res = await apiClient.post<ApiResponse<AuthTokenResponse>>(
      `${AUTH_BASE_URL}/register`,
      { name, email, password },
      { baseURL: '' }
    )
    const data = res.data.data
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
    return data
  },

  async login(email: string, password: string): Promise<AuthTokenResponse> {
    const res = await apiClient.post<ApiResponse<AuthTokenResponse>>(
      `${AUTH_BASE_URL}/login`,
      { email, password },
      { baseURL: '' }
    )
    const data = res.data.data
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
    return data
  },

  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    try {
      await apiClient.post(
        `${AUTH_BASE_URL}/logout`,
        { refresh_token: refreshToken },
        { baseURL: '' }
      )
    } catch {
      // ignore server errors during local logout
    } finally {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
  },

  async getMe(): Promise<AuthUser> {
    const res = await apiClient.get<ApiResponse<AuthUser>>(`${AUTH_BASE_URL}/me`, { baseURL: '' })
    return res.data.data
  },

  async listSessions(search?: string): Promise<MongoChatSession[]> {
    const res = await apiClient.get<ApiResponse<MongoChatSession[]>>('/sessions', {
      params: search ? { search } : undefined,
    })
    return res.data.data
  },

  async createSession(title = 'New Chat', conversationId?: string): Promise<MongoChatSession> {
    const res = await apiClient.post<ApiResponse<MongoChatSession>>('/sessions', {
      title,
      conversation_id: conversationId,
    })
    return res.data.data
  },

  async getSession(conversationId: string): Promise<MongoChatSession> {
    const res = await apiClient.get<ApiResponse<MongoChatSession>>(`/sessions/${conversationId}`)
    return res.data.data
  },

  async updateSession(
    conversationId: string,
    payload: { title?: string; is_pinned?: boolean }
  ): Promise<MongoChatSession> {
    const res = await apiClient.patch<ApiResponse<MongoChatSession>>(
      `/sessions/${conversationId}`,
      payload
    )
    return res.data.data
  },

  async deleteSession(conversationId: string): Promise<void> {
    await apiClient.delete(`/sessions/${conversationId}`)
  },

  async getUserSettings(): Promise<UserSettings> {
    const res = await apiClient.get<ApiResponse<UserSettings>>('/user/settings')
    return res.data.data
  },

  async updateUserSettings(settings: UserSettings): Promise<UserSettings> {
    const res = await apiClient.put<ApiResponse<UserSettings>>('/user/settings', settings)
    return res.data.data
  },
}

export default authService


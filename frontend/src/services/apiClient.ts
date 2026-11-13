import axios, { type AxiosError, type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'

const RAW_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()
const CLEAN_URL = RAW_URL.replace(/\/+$/, '')

export const API_BASE_URL = CLEAN_URL
  ? (CLEAN_URL.endsWith('/api/v1') ? CLEAN_URL : `${CLEAN_URL}/api/v1`)
  : '/api/v1'

export const AUTH_BASE_URL = CLEAN_URL
  ? (CLEAN_URL.endsWith('/api/v1') ? `${CLEAN_URL.slice(0, -7)}/api/auth` : `${CLEAN_URL}/api/auth`)
  : '/api/auth'

export const ACCESS_TOKEN_KEY = 'docmind_access_token'
export const REFRESH_TOKEN_KEY = 'docmind_refresh_token'

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Request interceptor: attach JWT Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let refreshQueue: Array<(token: string | null) => void> = []

function resolveRefreshQueue(token: string | null) {
  refreshQueue.forEach((cb) => cb(token))
  refreshQueue = []
}

// Response interceptor: silent refresh on 401 & structured error formatting
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalReq = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined

    if (error.response?.status === 401 && originalReq && !originalReq._retry) {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (refreshToken && !String(originalReq.url || '').includes('/auth/')) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            refreshQueue.push((newToken) => {
              if (!newToken) return reject(error)
              originalReq.headers = { ...(originalReq.headers || {}), Authorization: `Bearer ${newToken}` }
              resolve(apiClient(originalReq))
            })
          })
        }

        originalReq._retry = true
        isRefreshing = true
        try {
          const res = await axios.post(
            `${AUTH_BASE_URL}/refresh`,
            { refresh_token: refreshToken },
            { withCredentials: true }
          )
          const data = res.data?.data
          if (data?.access_token) {
            localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
            if (data.refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
            resolveRefreshQueue(data.access_token)
            originalReq.headers = { ...(originalReq.headers || {}), Authorization: `Bearer ${data.access_token}` }
            return apiClient(originalReq)
          }
        } catch {
          resolveRefreshQueue(null)
          localStorage.removeItem(ACCESS_TOKEN_KEY)
          localStorage.removeItem(REFRESH_TOKEN_KEY)
          window.dispatchEvent(new CustomEvent('docmind:auth-expired'))
        } finally {
          isRefreshing = false
        }
      } else if (!String(originalReq.url || '').includes('/auth/')) {
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        window.dispatchEvent(new CustomEvent('docmind:auth-expired'))
      }
    }

    let errorMessage = 'An unexpected error occurred while communicating with the server.'
    if (error.response?.data) {
      const data = error.response.data as any
      if (typeof data.detail === 'string') {
        errorMessage = data.detail
      } else if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ')
      } else if (data.message) {
        errorMessage = data.message
      }
    } else if (error.message) {
      errorMessage = error.message
    }

    return Promise.reject(new Error(errorMessage))
  }
)

export default apiClient

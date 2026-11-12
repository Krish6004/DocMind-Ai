import axios, { type AxiosError, type AxiosInstance, type AxiosResponse } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Allows injecting auth token or custom telemetry headers in the future
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
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

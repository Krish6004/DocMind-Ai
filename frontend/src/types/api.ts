/**
 * Standard API response envelope and error types.
 */

export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
  request_id?: string
}

export interface ApiError {
  detail: string | { [key: string]: any }
  status?: number
  code?: string
}

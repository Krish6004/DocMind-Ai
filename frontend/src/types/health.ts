/**
 * Health check data contract matching GET /api/v1/health.
 */

export interface SystemServicesStatus {
  api: 'operational' | 'degraded' | 'offline' | string
  ai_engine: 'ready' | 'loading' | 'offline' | string
  storage: 'available' | 'readonly' | 'offline' | string
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'offline' | string
  version: string
  environment: string
  timestamp: string
  services: SystemServicesStatus
}

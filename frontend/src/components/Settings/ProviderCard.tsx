import React, { useState } from 'react'
import {
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Settings,
  Clock,
  Cpu,
} from 'lucide-react'
import Button from '@/components/common/Button'
import ProviderLogo from '@/components/common/ProviderLogo'
import type { ProviderInfo } from '@/types'
import providerService from '@/services/providerService'
import { useToast } from '@/hooks/useToast'

interface ProviderCardProps {
  provider: ProviderInfo
  onConfigure: (provider: ProviderInfo) => void
  onUpdated: () => void
}

export const ProviderCard: React.FC<ProviderCardProps> = ({
  provider,
  onConfigure,
  onUpdated,
}) => {
  const { success, error: toastError } = useToast()

  const [isTesting, setIsTesting] = useState(false)
  const [latency, setLatency] = useState<number | null>(provider.last_latency_ms)
  const [currentStatus, setCurrentStatus] = useState(provider.status)
  const [isUpdatingModel, setIsUpdatingModel] = useState(false)

  const isComingSoon = provider.is_coming_soon || provider.status === 'Coming Soon'
  const isConnected = currentStatus === 'Connected' || currentStatus === 'connected' || provider.has_api_key

  const handleTestConnection = async () => {
    if (isComingSoon) return
    setIsTesting(true)
    try {
      const res = await providerService.testProvider(provider.id)
      setCurrentStatus(res.status)
      setLatency(res.latency_ms)
      if (res.status === 'Connected' || res.status === 'connected') {
        success(`${provider.name} Connected`, `Ping latency: ${res.latency_ms}ms · Model: ${res.model}`)
      } else {
        toastError(`${provider.name} Test Failed`, res.message || 'Credentials not accepted by provider endpoint.')
      }
      onUpdated()
    } catch (err: any) {
      setCurrentStatus('Failed')
      toastError('Connection Error', err.message || 'Network error reaching provider.')
    } finally {
      setIsTesting(false)
    }
  }

  const handleModelChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (isComingSoon) return
    const newModel = e.target.value
    setIsUpdatingModel(true)
    try {
      await providerService.updateProvider(provider.id, {
        selected_model: newModel,
      })
      success('Model Updated', `${provider.name} model set to ${newModel}`)
      onUpdated()
    } catch (err: any) {
      toastError('Update Failed', err.message || 'Failed to update model.')
    } finally {
      setIsUpdatingModel(false)
    }
  }

  return (
    <div
      className={`rounded-2xl border p-6 flex flex-col justify-between space-y-5 transition-all ${
        isComingSoon
          ? 'bg-jet-950/40 border-white/[0.04] opacity-75'
          : provider.is_default
          ? 'bg-jet-950/80 border-cerulean/40 ring-1 ring-cerulean/20 shadow-glass-sm'
          : 'bg-jet-950/70 border-white/[0.08] hover:border-white/[0.14]'
      }`}
    >
      {/* Top Identity & Status */}
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center space-x-3.5">
            <ProviderLogo providerId={provider.id} size="lg" />
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-semibold text-white tracking-tight">
                  {provider.name}
                </h3>

                {provider.is_default && (
                  <span className="text-[10px] font-mono uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-medium">
                    Default
                  </span>
                )}

                {provider.is_fallback && (
                  <span className="text-[10px] font-mono uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full font-medium">
                    Fallback
                  </span>
                )}

                {isComingSoon && (
                  <span className="text-[10px] font-mono uppercase bg-white/[0.06] text-jet-400 border border-white/[0.08] px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5" />
                    Coming Soon
                  </span>
                )}
              </div>

              <p className="text-xs text-jet-400 mt-0.5">{provider.tagline}</p>
            </div>
          </div>
        </div>

        {/* Short Description */}
        <p className="text-xs text-jet-300 leading-relaxed">
          {provider.description}
        </p>

        {/* Connection Status & Metadata Matrix */}
        <div className="p-3.5 rounded-xl bg-jet-900/60 border border-white/[0.06] space-y-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-mono text-jet-400">Status:</span>
            <div className="flex items-center space-x-1.5">
              {isComingSoon ? (
                <span className="text-jet-500 font-mono text-xs">Coming Soon</span>
              ) : (
                <>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-jet-600'
                    }`}
                  />
                  <span
                    className={`font-medium ${
                      isConnected ? 'text-emerald-400' : 'text-jet-400'
                    }`}
                  >
                    {isConnected ? '✓ Connected' : 'Not Connected'}
                  </span>
                  {latency && isConnected && (
                    <span className="font-mono text-[10px] text-jet-400 ml-1">
                      ({latency}ms)
                    </span>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-xs pt-1.5 border-t border-white/[0.04]">
            <span className="font-mono text-jet-400">Credential Source:</span>
            <span className="text-jet-300 font-mono text-[11px]">
              Backend (.env)
            </span>
          </div>
        </div>

        {/* Model Selector */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs font-mono text-jet-400">
            <span>Model:</span>
            {isComingSoon ? (
              <span className="text-[10px] text-jet-600">Unavailable</span>
            ) : (
              <span className="text-[10px] text-jet-500">Tested Grounding</span>
            )}
          </div>
          {isComingSoon ? (
            <div className="w-full px-3 py-2 rounded-xl bg-jet-900/40 border border-white/[0.04] text-xs text-jet-500 font-mono">
              {provider.active_model || 'Coming Soon'}
            </div>
          ) : (
            <select
              value={provider.selected_model || provider.active_model}
              onChange={handleModelChange}
              disabled={isUpdatingModel}
              className="w-full px-3 py-2 rounded-xl bg-jet-900 border border-white/[0.1] text-xs text-white focus:outline-none focus:border-cerulean transition-colors font-mono cursor-pointer disabled:opacity-50"
            >
              {provider.supported_models.map((m) => (
                <option key={m} value={m} className="bg-jet-950 text-white">
                  {m}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Buttons: Configure & Test Connection */}
      <div className="flex items-center justify-between pt-4 border-t border-white/[0.06] gap-3">
        <Button
          variant="glass"
          size="sm"
          onClick={() => onConfigure(provider)}
          disabled={isComingSoon}
          leftIcon={<Settings className="w-3.5 h-3.5" />}
          className="text-xs flex-1 border-white/10 hover:border-white/20 disabled:opacity-40"
        >
          Configure
        </Button>

        <Button
          variant={isConnected ? 'glass' : 'cerulean'}
          size="sm"
          onClick={handleTestConnection}
          disabled={isTesting || isComingSoon}
          leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />}
          className="text-xs flex-1 disabled:opacity-40"
        >
          {isTesting ? 'Testing...' : 'Test Connection'}
        </Button>
      </div>
    </div>
  )
}

export default ProviderCard

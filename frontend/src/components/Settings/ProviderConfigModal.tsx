import React, { useState, useEffect } from 'react'
import {
  X,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Server,
  Cpu,
  Layers,
} from 'lucide-react'
import Button from '@/components/common/Button'
import ProviderLogo from '@/components/common/ProviderLogo'
import type { ProviderInfo } from '@/types'
import providerService from '@/services/providerService'
import { useToast } from '@/hooks/useToast'

interface ProviderConfigModalProps {
  provider: ProviderInfo | null
  isOpen: boolean
  onClose: () => void
  onSaved: () => void
}

export const ProviderConfigModal: React.FC<ProviderConfigModalProps> = ({
  provider,
  isOpen,
  onClose,
  onSaved,
}) => {
  const { success, error: toastError } = useToast()

  const [selectedModel, setSelectedModel] = useState('')
  const [isUpdatingModel, setIsUpdatingModel] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<{
    success: boolean
    status: string
    message: string
    latency_ms?: number | null
    model?: string
  } | null>(null)

  useEffect(() => {
    if (provider) {
      setSelectedModel(provider.selected_model || provider.active_model)
      setTestResult(null)
    }
  }, [provider])

  if (!isOpen || !provider) return null

  const isConnected = provider.status === 'Connected' || provider.has_api_key

  const handleTestConnection = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const res = await providerService.testProvider(provider.id, {
        model: selectedModel.trim() || undefined,
      })
      const isOk = res.status === 'Connected' || res.status === 'connected'
      setTestResult({
        success: isOk,
        status: res.status,
        message: res.message || (isOk ? 'Connection verified successfully.' : 'Connection check failed.'),
        latency_ms: res.latency_ms,
        model: res.model,
      })
      if (isOk) {
        success('Connection Verified', `Latency: ${res.latency_ms}ms · Model: ${res.model}`)
      } else {
        toastError('Verification Failed', res.message || 'Provider rejected ping.')
      }
      onSaved()
    } catch (err: any) {
      setTestResult({
        success: false,
        status: 'Failed',
        message: err.message || 'Network error reaching provider endpoint.',
      })
      toastError('Connection Error', err.message || 'Failed to ping provider')
    } finally {
      setIsTesting(false)
    }
  }

  const handleModelChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newModel = e.target.value
    setSelectedModel(newModel)
    setIsUpdatingModel(true)
    try {
      await providerService.updateProvider(provider.id, {
        selected_model: newModel,
      })
      success('Model Updated', `${provider.name} active model changed to ${newModel}`)
      onSaved()
    } catch (err: any) {
      toastError('Model Update Failed', err.message || 'Could not update model.')
    } finally {
      setIsUpdatingModel(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-white/10 p-6 sm:p-7 shadow-2xl bg-jet-950 text-white space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center space-x-3.5">
            <ProviderLogo providerId={provider.id} size="md" />
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
              </div>
              <p className="text-xs text-jet-400 mt-0.5">{provider.tagline}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-jet-400 hover:text-white hover:bg-white/[0.08] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Read-Only Configuration Matrix */}
        <div className="space-y-4">
          {/* Provider */}
          <div className="p-3.5 rounded-xl bg-jet-900/60 border border-white/[0.06] flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <Layers className="w-4 h-4 text-jet-400" />
              <span className="text-xs font-mono uppercase tracking-wider text-jet-400">
                Provider
              </span>
            </div>
            <span className="text-xs font-semibold text-white">
              {provider.name}
            </span>
          </div>

          {/* Credential Source */}
          <div className="p-3.5 rounded-xl bg-jet-900/60 border border-white/[0.06] flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <Server className="w-4 h-4 text-cerulean-light" />
              <span className="text-xs font-mono uppercase tracking-wider text-jet-400">
                Credential Source
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono text-white bg-white/[0.06] px-2 py-0.5 rounded-md border border-white/[0.08]">
                Backend (.env)
              </span>
            </div>
          </div>

          {/* Connection */}
          <div className="p-3.5 rounded-xl bg-jet-900/60 border border-white/[0.06] flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-jet-400">
              Connection
            </span>
            <div className="flex items-center space-x-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-jet-600'
                }`}
              />
              <span
                className={`text-xs font-medium font-mono ${
                  isConnected ? 'text-emerald-400' : 'text-jet-400'
                }`}
              >
                {isConnected ? 'Connected' : 'Not Configured'}
              </span>
            </div>
          </div>

          {/* Active Model */}
          <div className="p-3.5 rounded-xl bg-jet-900/60 border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Cpu className="w-4 h-4 text-neonrose" />
                <span className="text-xs font-mono uppercase tracking-wider text-jet-400">
                  Active Model
                </span>
              </div>
              <span className="text-[10px] text-jet-500 font-mono">
                {isUpdatingModel ? 'Updating...' : 'Selectable'}
              </span>
            </div>
            <select
              value={selectedModel}
              onChange={handleModelChange}
              disabled={isUpdatingModel}
              className="w-full px-3 py-2 rounded-xl bg-jet-950 border border-white/[0.1] text-xs text-white focus:outline-none focus:border-cerulean transition-colors font-mono cursor-pointer disabled:opacity-50"
            >
              {provider.supported_models.map((m) => (
                <option key={m} value={m} className="bg-jet-950 text-white">
                  {m}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Test Result Display */}
        {testResult && (
          <div
            className={`p-3.5 rounded-xl border text-xs flex items-center justify-between ${
              testResult.success
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                : 'bg-red-500/10 border-red-500/20 text-red-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              {testResult.success ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              )}
              <span className="truncate">{testResult.message}</span>
            </div>
            {testResult.latency_ms && (
              <span className="font-mono text-[11px] shrink-0 ml-2">
                {testResult.latency_ms}ms
              </span>
            )}
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-white/[0.08]">
          <Button
            variant="cerulean"
            size="sm"
            onClick={handleTestConnection}
            disabled={isTesting || !isConnected}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />}
            className="text-xs font-semibold px-4"
          >
            {isTesting ? 'Testing...' : 'Test Connection'}
          </Button>

          <Button
            variant="glass"
            size="sm"
            onClick={onClose}
            className="text-xs border-white/10 hover:border-white/20"
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}

export default ProviderConfigModal

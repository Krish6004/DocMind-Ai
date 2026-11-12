import React, { useState } from 'react'
import {
  ArrowDown,
  ArrowUp,
  ChevronRight,
  ShieldAlert,
  Sliders,
  Check,
  RefreshCw,
} from 'lucide-react'
import Button from '@/components/common/Button'
import ProviderLogo from '@/components/common/ProviderLogo'
import type { ProviderInfo } from '@/types'
import providerService from '@/services/providerService'
import { useToast } from '@/hooks/useToast'

interface ProviderPriorityWaterfallProps {
  providers: ProviderInfo[]
  priorityOrder: string[]
  activeProvider: string
  onPriorityChanged: () => void
}

export const ProviderPriorityWaterfall: React.FC<ProviderPriorityWaterfallProps> = ({
  providers,
  priorityOrder,
  activeProvider,
  onPriorityChanged,
}) => {
  const { success, error: toastError } = useToast()
  const [order, setOrder] = useState<string[]>(priorityOrder)
  const [isSaving, setIsSaving] = useState(false)

  // Keep internal state synced when props change
  React.useEffect(() => {
    setOrder(priorityOrder)
  }, [priorityOrder])

  const moveUp = (index: number) => {
    if (index === 0) return
    const newOrder = [...order]
    const temp = newOrder[index - 1]
    newOrder[index - 1] = newOrder[index]
    newOrder[index] = temp
    setOrder(newOrder)
  }

  const moveDown = (index: number) => {
    if (index === order.length - 1) return
    const newOrder = [...order]
    const temp = newOrder[index + 1]
    newOrder[index + 1] = newOrder[index]
    newOrder[index] = temp
    setOrder(newOrder)
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await providerService.updatePriorityOrder({
        priority_order: order,
      })
      success('Priority Cascade Updated', 'Automatic fallback sequence saved successfully.')
      onPriorityChanged()
    } catch (err: any) {
      toastError('Update Failed', err.message || 'Failed to update priority order.')
    } finally {
      setIsSaving(false)
    }
  }

  const providerMap = new Map(providers.map((p) => [p.id, p]))
  const isDirty = JSON.stringify(order) !== JSON.stringify(priorityOrder)

  return (
    <div className="rounded-2xl glass-panel border border-white/[0.08] p-5 sm:p-6 space-y-5 bg-jet-950/80">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-cerulean-light" />
            <h3 className="text-sm font-semibold text-white tracking-tight">
              Cascading Provider Fallback Priority
            </h3>
          </div>
          <p className="text-xs text-jet-400 mt-0.5">
            If the primary provider encounters rate limits, downtime, or network disruption, requests automatically cascade down the chain.
          </p>
        </div>

        {isDirty && (
          <Button
            variant="cerulean"
            size="sm"
            onClick={handleSave}
            disabled={isSaving}
            leftIcon={<Check className="w-3.5 h-3.5" />}
            className="text-xs shrink-0"
          >
            {isSaving ? 'Saving...' : 'Apply Priority Order'}
          </Button>
        )}
      </div>

      {/* Waterfall Sequence Row */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5">
        {order.map((pid, idx) => {
          const provider = providerMap.get(pid)
          if (!provider) return null

          const isPrimary = pid === activeProvider
          const isConnected = provider.has_api_key

          return (
            <div
              key={pid}
              className={`p-3 rounded-xl border flex flex-col justify-between space-y-2 transition-all ${
                isPrimary
                  ? 'bg-cerulean/10 border-cerulean/40 text-white shadow-glass-sm'
                  : 'bg-jet-900/70 border-white/[0.06] text-jet-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-jet-400 px-1.5 py-0.5 rounded bg-white/[0.04]">
                  Rank #{idx + 1}
                </span>

                <div className="flex items-center space-x-1">
                  <button
                    type="button"
                    onClick={() => moveUp(idx)}
                    disabled={idx === 0}
                    className="p-1 rounded text-jet-400 hover:text-white disabled:opacity-20 hover:bg-white/[0.05]"
                    title="Move higher priority"
                  >
                    <ArrowUp className="w-3 h-3" />
                  </button>
                  <button
                    type="button"
                    onClick={() => moveDown(idx)}
                    disabled={idx === order.length - 1}
                    className="p-1 rounded text-jet-400 hover:text-white disabled:opacity-20 hover:bg-white/[0.05]"
                    title="Move lower priority"
                  >
                    <ArrowDown className="w-3 h-3" />
                  </button>
                </div>
              </div>

              <div className="flex items-center space-x-2.5">
                <ProviderLogo providerId={pid} size="sm" />
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-white truncate">
                    {provider.name}
                  </div>
                  <div className="text-[10px] font-mono text-jet-400 truncate">
                    {provider.selected_model}
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[10px]">
                <span className={`inline-flex items-center gap-1 ${
                  isConnected ? 'text-emerald-400' : 'text-jet-500'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-jet-600'}`} />
                  {isConnected ? 'Key Ready' : 'Unconfigured'}
                </span>

                {isPrimary && (
                  <span className="text-[9px] font-mono uppercase text-cerulean-light font-bold">
                    Primary
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ProviderPriorityWaterfall


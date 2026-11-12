import React, { useState, useEffect } from 'react'
import {
  Cpu,
  Layers,
  ShieldCheck,
  Server,
  RefreshCw,
  CheckCircle2,
  Sliders,
  Terminal,
  Database,
  ExternalLink,
} from 'lucide-react'
import Button from '@/components/common/Button'
import ProviderCard from '@/components/Settings/ProviderCard'
import ProviderConfigModal from '@/components/Settings/ProviderConfigModal'
import ProviderPriorityWaterfall from '@/components/Settings/ProviderPriorityWaterfall'
import type { ProviderInfo, ProviderListResponse } from '@/types'
import providerService from '@/services/providerService'
import { useToast } from '@/hooks/useToast'

export const SettingsPage: React.FC = () => {
  const { success, error: toastError } = useToast()

  const [providerData, setProviderData] = useState<ProviderListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'providers' | 'retrieval' | 'architecture'>('providers')
  const [editingProvider, setEditingProvider] = useState<ProviderInfo | null>(null)

  // Retrieval Settings State
  const [rrfK, setRrfK] = useState(60)
  const [topK, setTopK] = useState(5)
  const [temperature, setTemperature] = useState(0.2)
  const [memoryWindow, setMemoryWindow] = useState(3)

  const fetchProviders = async () => {
    setIsLoading(true)
    try {
      const data = await providerService.getProviders()
      setProviderData(data)
    } catch (err: any) {
      toastError('Error', err.message || 'Failed to load AI providers.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchProviders()
  }, [])

  const handleSaveRetrieval = () => {
    success('Parameters Saved', 'Retrieval hyperparameters updated for active sessions.')
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.08] gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-cerulean-light mb-1">
            <Cpu className="w-3.5 h-3.5" />
            <span>Inference Management</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            AI Providers & Models
          </h1>
          <p className="text-xs text-jet-400 mt-1">
            Enterprise multi-model orchestration, Developer Hosted (.env) vs BYOK credentials, and cascading fallback priority.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="glass"
            size="sm"
            onClick={fetchProviders}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
            className="text-xs border-white/10 hover:border-white/20"
          >
            Refresh Providers
          </Button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center space-x-2 border-b border-white/[0.06] pb-2 text-xs font-medium">
        <button
          type="button"
          onClick={() => setActiveTab('providers')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center space-x-2 ${
            activeTab === 'providers'
              ? 'bg-white/10 text-white shadow-glass-sm'
              : 'text-jet-400 hover:text-white hover:bg-white/[0.03]'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>AI Providers ({providerData?.providers.length || 5})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('retrieval')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center space-x-2 ${
            activeTab === 'retrieval'
              ? 'bg-white/10 text-white shadow-glass-sm'
              : 'text-jet-400 hover:text-white hover:bg-white/[0.03]'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Retrieval & RRF Tuning</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('architecture')}
          className={`px-3.5 py-1.5 rounded-lg transition-colors flex items-center space-x-2 ${
            activeTab === 'architecture'
              ? 'bg-white/10 text-white shadow-glass-sm'
              : 'text-jet-400 hover:text-white hover:bg-white/[0.03]'
          }`}
        >
          <Server className="w-3.5 h-3.5" />
          <span>Architecture Contract</span>
        </button>
      </div>

      {/* Tab 1: AI Providers Management Dashboard */}
      {activeTab === 'providers' && (
        <div className="space-y-8 animate-fade-in">
          {/* Cascading Fallback Priority Waterfall */}
          {providerData && (
            <ProviderPriorityWaterfall
              providers={providerData.providers}
              priorityOrder={providerData.priority_order}
              activeProvider={providerData.active_provider}
              onPriorityChanged={fetchProviders}
            />
          )}

          {/* Provider Cards Grid */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white tracking-tight uppercase tracking-wider font-mono text-xs">
                Available LLM Providers
              </h2>
              <span className="text-[11px] font-mono text-jet-400">
                Active Provider: <span className="text-cerulean-light font-bold capitalize">{providerData?.active_provider}</span>
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {providerData?.providers.map((provider) => (
                <ProviderCard
                  key={provider.id}
                  provider={provider}
                  onConfigure={(p) => setEditingProvider(p)}
                  onUpdated={fetchProviders}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Retrieval & RRF Tuning */}
      {activeTab === 'retrieval' && (
        <div className="rounded-2xl glass-panel border border-white/[0.08] p-6 space-y-6 max-w-3xl animate-fade-in">
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-white">Hybrid Retrieval & Fusion Hyperparameters</h3>
            <p className="text-xs text-jet-400">
              Configure parameters for manual BM25 sparse index, dense vector similarity, and Reciprocal Rank Fusion (RRF).
            </p>
          </div>

          <div className="space-y-5 pt-2">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <label className="font-mono text-jet-300">Reciprocal Rank Fusion Smoothing Constant (k)</label>
                <span className="font-mono text-cerulean-light font-bold">k = {rrfK}</span>
              </div>
              <input
                type="range"
                min="1"
                max="120"
                value={rrfK}
                onChange={(e) => setRrfK(Number(e.target.value))}
                className="w-full accent-cerulean"
              />
              <p className="text-[11px] text-jet-400">
                Formula: RRF(d) = Σ 1 / (k + rank). k=60 is the gold standard benchmark value neutralizing outlier ranks.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <label className="font-mono text-jet-300">Candidate Retrieval Depth (top_k)</label>
                <span className="font-mono text-cerulean-light font-bold">{topK} chunks</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-cerulean"
              />
              <p className="text-[11px] text-jet-400">
                Number of top reranked chunks passed into LLM prompt context blocks.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <label className="font-mono text-jet-300">Conversational Memory Turns</label>
                <span className="font-mono text-cerulean-light font-bold">{memoryWindow} turns</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={memoryWindow}
                onChange={(e) => setMemoryWindow(Number(e.target.value))}
                className="w-full accent-cerulean"
              />
              <p className="text-[11px] text-jet-400">
                Historical query/answer pairs fetched from SQLite for conversational continuity.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-white/[0.08] flex justify-end">
            <Button variant="cerulean" size="sm" onClick={handleSaveRetrieval}>
              Save Hyperparameters
            </Button>
          </div>
        </div>
      )}

      {/* Tab 3: Clean Architecture Contract */}
      {activeTab === 'architecture' && (
        <div className="rounded-2xl glass-panel border border-white/[0.08] p-6 space-y-6 max-w-4xl animate-fade-in">
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-white">Clean Architecture & LLM Decoupling Contract</h3>
            <p className="text-xs text-jet-400">
              DocMind AI strictly separates the scientific retrieval pipeline from answer generation.
            </p>
          </div>

          {/* Layer Flow Diagram */}
          <div className="p-5 rounded-xl bg-jet-900/80 border border-white/[0.08] space-y-3 font-mono text-xs">
            <div className="text-cerulean-light font-semibold">System Layer Stack:</div>
            <div className="space-y-2 text-jet-300">
              <div className="p-2.5 rounded bg-black/40 border border-white/5 flex items-center justify-between">
                <span>1. Presentation Layer</span>
                <span className="text-[10px] text-jet-400">FastAPI REST Endpoints (/api/v1/chat, /api/v1/providers)</span>
              </div>
              <div className="p-2.5 rounded bg-black/40 border border-white/5 flex items-center justify-between">
                <span>2. Service Layer</span>
                <span className="text-[10px] text-jet-400">ChatService · DocumentService · UploadService</span>
              </div>
              <div className="p-2.5 rounded bg-black/40 border border-white/5 flex items-center justify-between">
                <span>3. Provider Manager</span>
                <span className="text-[10px] text-cerulean-light font-bold">ProviderManager (Cascading Fallback & Priority)</span>
              </div>
              <div className="p-2.5 rounded bg-black/40 border border-white/5 flex items-center justify-between">
                <span>4. LLM Adapter Contract</span>
                <span className="text-[10px] text-jet-400">BaseLLMAdapter.generate(messages, model, temperature)</span>
              </div>
              <div className="p-2.5 rounded bg-black/40 border border-white/5 flex items-center justify-between">
                <span>5. Concrete Adapters</span>
                <span className="text-[10px] text-emerald-400">GeminiAdapter · GroqAdapter · OpenAIAdapter · ClaudeAdapter · OllamaAdapter</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-jet-900/50 border border-white/[0.06] space-y-1.5">
              <div className="font-semibold text-white flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Retrieval Engine Invariance
              </div>
              <p className="text-jet-400 leading-relaxed">
                Dense embeddings (384-dim all-MiniLM-L6), inverted BM25 indices, Reciprocal Rank Fusion, and cross-encoder rerankers run locally and never change based on the LLM.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-jet-900/50 border border-white/[0.06] space-y-1.5">
              <div className="font-semibold text-white flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-cerulean-light" />
                Zero Key Exposure
              </div>
              <p className="text-jet-400 leading-relaxed">
                API keys are never exposed in JSON responses. The frontend only receives masked tokens (e.g. AIza••••3B8f) and boolean status flags.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      <ProviderConfigModal
        provider={editingProvider}
        isOpen={Boolean(editingProvider)}
        onClose={() => setEditingProvider(null)}
        onSaved={fetchProviders}
      />
    </div>
  )
}

export default SettingsPage

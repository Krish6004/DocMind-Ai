import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MessageSquare,
  Upload,
} from 'lucide-react'
import Button from '@/components/common/Button'
import Badge from '@/components/common/Badge'
import type { HealthResponse } from '@/types'

interface HeroProps {
  health?: HealthResponse
  isLoading?: boolean
  isError?: boolean
  onRefresh?: () => void
}

export const Hero: React.FC<HeroProps> = () => {
  const navigate = useNavigate()

  return (
    <div className="relative overflow-hidden rounded-2xl glass-panel p-6 sm:p-8 border border-white/[0.08]">
      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        {/* Left: Headline & Description */}
        <div className="space-y-3 max-w-2xl">
          <div className="flex items-center space-x-2.5">
            <Badge variant="cerulean" size="sm">
              Hybrid RAG Engine
            </Badge>
            <span className="text-xs text-jet-400 font-mono">
              BGE-small · BM25 · ms-marco
            </span>
          </div>

          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Grounded Document Intelligence
            </h1>
            <p className="text-xs sm:text-sm text-jet-300 mt-1.5 leading-relaxed">
              Synthesize organizational knowledge with reciprocal rank fusion (RRF k=60), calibrated confidence scores, and sub-second grounded answers.
            </p>
          </div>
        </div>

        {/* Right: Primary Call to Actions */}
        <div className="flex items-center space-x-3 shrink-0">
          <Button
            variant="cerulean"
            size="md"
            leftIcon={<MessageSquare className="w-4 h-4" />}
            onClick={() => navigate('/chat')}
            className="shadow-glow-cerulean/20"
          >
            Start Chat
          </Button>

          <Button
            variant="glass"
            size="md"
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => navigate('/documents')}
          >
            Upload Docs
          </Button>
        </div>
      </div>
    </div>
  )
}

export default Hero

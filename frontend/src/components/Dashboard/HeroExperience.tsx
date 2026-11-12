import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import {
  MessageSquare,
  Upload,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Zap,
  Search,
} from 'lucide-react'
import Logo from '@/components/common/Logo'
import Button from '@/components/common/Button'
import type { HealthResponse } from '@/types'

interface HeroExperienceProps {
  health?: HealthResponse
  isLoading?: boolean
  isError?: boolean
}

export const HeroExperience: React.FC<HeroExperienceProps> = ({
  health,
  isLoading,
  isError,
}) => {
  const navigate = useNavigate()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  // Mouse reactive tracking for lighting and tilt
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  const springConfig = { damping: 25, stiffness: 120 }
  const smoothMouseX = useSpring(mouseX, springConfig)
  const smoothMouseY = useSpring(mouseY, springConfig)

  const rotateX = useTransform(smoothMouseY, [-300, 300], [6, -6])
  const rotateY = useTransform(smoothMouseX, [-500, 500], [-6, 6])

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left - rect.width / 2
    const y = e.clientY - rect.top - rect.height / 2
    mouseX.set(x)
    mouseY.set(y)
  }

  // Interactive 3D Knowledge Orb / Constellation Canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    let width = (canvas.width = canvas.offsetWidth)
    let height = (canvas.height = canvas.offsetHeight)

    const handleResize = () => {
      if (!canvas) return
      width = canvas.width = canvas.offsetWidth
      height = canvas.height = canvas.offsetHeight
    }

    window.addEventListener('resize', handleResize)

    // Particle nodes for the neural knowledge sphere
    const nodeCount = 52
    const nodes: Array<{
      x: number
      y: number
      z: number
      baseX: number
      baseY: number
      baseZ: number
      radius: number
      color: string
    }> = []

    const sphereRadius = Math.min(width, height) * 0.32

    for (let i = 0; i < nodeCount; i++) {
      const phi = Math.acos(-1 + (2 * i) / nodeCount)
      const theta = Math.sqrt(nodeCount * Math.PI) * phi

      const x = sphereRadius * Math.cos(theta) * Math.sin(phi)
      const y = sphereRadius * Math.sin(theta) * Math.sin(phi)
      const z = sphereRadius * Math.cos(phi)

      nodes.push({
        x,
        y,
        z,
        baseX: x,
        baseY: y,
        baseZ: z,
        radius: Math.random() * 1.8 + 1.2,
        color: i % 4 === 0 ? '#FF2D95' : i % 2 === 0 ? '#189FD2' : '#007BA7',
      })
    }

    let angleY = 0
    let angleX = 0

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Center origin
      const centerX = width * 0.72
      const centerY = height * 0.48

      angleY += 0.003
      angleX += 0.0015

      // Soft ambient core glow
      const radialGlow = ctx.createRadialGradient(
        centerX,
        centerY,
        10,
        centerX,
        centerY,
        sphereRadius * 1.5
      )
      radialGlow.addColorStop(0, 'rgba(0, 123, 167, 0.18)')
      radialGlow.addColorStop(0.5, 'rgba(24, 159, 210, 0.06)')
      radialGlow.addColorStop(0.8, 'rgba(255, 45, 149, 0.03)')
      radialGlow.addColorStop(1, 'transparent')
      ctx.fillStyle = radialGlow
      ctx.beginPath()
      ctx.arc(centerX, centerY, sphereRadius * 1.5, 0, Math.PI * 2)
      ctx.fill()

      // Project and rotate nodes
      const projectedNodes: Array<{
        px: number
        py: number
        pz: number
        radius: number
        color: string
      }> = []

      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i]

        // Rotation around Y
        const cosY = Math.cos(angleY)
        const sinY = Math.sin(angleY)
        const x1 = node.baseX * cosY - node.baseZ * sinY
        const z1 = node.baseZ * cosY + node.baseX * sinY

        // Rotation around X
        const cosX = Math.cos(angleX)
        const sinX = Math.sin(angleX)
        const y2 = node.baseY * cosX - z1 * sinX
        const z2 = z1 * cosX + node.baseY * sinX

        // Perspective projection
        const fov = 400
        const scale = fov / (fov + z2)
        const px = centerX + x1 * scale
        const py = centerY + y2 * scale

        projectedNodes.push({
          px,
          py,
          pz: z2,
          radius: node.radius * scale,
          color: node.color,
        })
      }

      // Draw connection lines between nearest neighbors
      ctx.lineWidth = 0.65
      for (let i = 0; i < projectedNodes.length; i++) {
        for (let j = i + 1; j < projectedNodes.length; j++) {
          const dx = projectedNodes[i].px - projectedNodes[j].px
          const dy = projectedNodes[i].py - projectedNodes[j].py
          const dist = Math.sqrt(dx * dx + dy * dy)

          if (dist < 72) {
            const alpha = (1 - dist / 72) * 0.35
            ctx.strokeStyle = `rgba(0, 123, 167, ${alpha})`
            ctx.beginPath()
            ctx.moveTo(projectedNodes[i].px, projectedNodes[i].py)
            ctx.lineTo(projectedNodes[j].px, projectedNodes[j].py)
            ctx.stroke()
          }
        }
      }

      // Draw nodes sorted by depth
      projectedNodes.sort((a, b) => a.pz - b.pz)

      for (const p of projectedNodes) {
        ctx.fillStyle = p.color
        ctx.shadowColor = p.color
        ctx.shadowBlur = 6
        ctx.beginPath()
        ctx.arc(p.px, p.py, Math.max(0.8, p.radius), 0, Math.PI * 2)
        ctx.fill()
        ctx.shadowBlur = 0
      }

      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  const isHealthy = health?.status === 'healthy'

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="relative min-h-[640px] lg:min-h-[700px] w-full rounded-3xl overflow-hidden glass-panel border border-white/[0.09] p-8 sm:p-12 lg:p-16 flex flex-col justify-between preserve-3d"
    >
      {/* 3D Knowledge Constellation Canvas Background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none opacity-85 z-0"
      />

      {/* Mouse reactive ambient spotlight */}
      <motion.div
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          background: useTransform(
            [smoothMouseX, smoothMouseY],
            ([x, y]) =>
              `radial-gradient(700px circle at ${Number(x) + 400}px ${
                Number(y) + 300
              }px, rgba(0, 123, 167, 0.12), transparent 70%)`
          ),
        }}
      />

      {/* Subtle Grid Accent */}
      <div className="absolute inset-0 bg-subtle-grid opacity-30 pointer-events-none z-0" />

      {/* Top Header Badge & System State */}
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-4">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center space-x-2.5 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/10 backdrop-blur-md shadow-glass-sm"
        >
          <span className="relative flex h-2 w-2">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isHealthy ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isHealthy ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
          </span>
          <span className="text-xs font-medium tracking-wide text-white">
            DocMind 2.0 Engine Active
          </span>
          <span className="text-jet-500 text-xs">/</span>
          <span className="text-xs font-mono text-cerulean-light">
            Reciprocal Rank Fusion
          </span>
        </motion.div>

        {/* Minimal Engine Attributes */}
        <div className="hidden sm:flex items-center space-x-4 text-xs font-mono text-jet-400">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cerulean" />
            all-MiniLM-L6 (384d)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-neonrose" />
            ms-marco Cross-Encoder
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-white/40" />
            Zero-Hallucination Grounding
          </span>
        </div>
      </div>

      {/* Center Hero Content & Storytelling */}
      <motion.div
        style={{ rotateX, rotateY }}
        className="relative z-10 max-w-2xl lg:max-w-3xl my-auto py-8 sm:py-12 preserve-3d"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="space-y-6"
        >
          {/* Hero Branding Mark */}
          <div className="inline-block mb-1">
            <Logo size="xl" showText={false} />
          </div>

          {/* Headline */}
          <div className="space-y-2">
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.08]">
              Knowledge, <br />
              <span className="text-shimmer">Reimagined.</span>
            </h1>
            <p className="text-base sm:text-lg lg:text-xl text-jet-300 font-normal leading-relaxed max-w-xl pt-2">
              Talk directly to your documents with mathematically grounded hybrid
              retrieval, cross-encoder neural reranking, and exact source
              citations.
            </p>
          </div>

          {/* Key Value Proposition Chips */}
          <div className="flex flex-wrap items-center gap-2.5 pt-1 text-xs text-jet-300">
            <span className="px-3 py-1 rounded-lg bg-white/[0.04] border border-white/[0.06] backdrop-blur-sm flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-cerulean-light" />
              100% Verifiable Citations
            </span>
            <span className="px-3 py-1 rounded-lg bg-white/[0.04] border border-white/[0.06] backdrop-blur-sm flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-neonrose" />
              Sub-150ms Hybrid RRF
            </span>
            <span className="px-3 py-1 rounded-lg bg-white/[0.04] border border-white/[0.06] backdrop-blur-sm flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-white/80" />
              Pure Python · No Framework Bloat
            </span>
          </div>

          {/* Primary Action Buttons */}
          <div className="flex flex-wrap items-center gap-4 pt-4">
            <Button
              variant="cerulean"
              size="lg"
              leftIcon={<MessageSquare className="w-5 h-5" />}
              rightIcon={<ArrowRight className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" />}
              onClick={() => navigate('/chat')}
              className="shadow-glow-cerulean text-sm font-semibold px-6 py-3.5 rounded-xl border border-cerulean-light/40 group hover:scale-[1.02] transition-all"
            >
              Start Chat Studio
            </Button>

            <Button
              variant="glass"
              size="lg"
              leftIcon={<Upload className="w-5 h-5 text-jet-300" />}
              onClick={() => navigate('/documents')}
              className="text-sm font-medium px-6 py-3.5 rounded-xl hover:bg-white/[0.08] border border-white/[0.12] transition-all"
            >
              Upload Documents
            </Button>

            <button
              type="button"
              onClick={() => {
                const searchEl = document.querySelector('header input') as HTMLInputElement | null
                if (searchEl) {
                  searchEl.focus()
                } else {
                  navigate('/chat')
                }
              }}
              className="hidden md:inline-flex items-center space-x-2 text-xs font-mono text-jet-400 hover:text-white px-3 py-2 rounded-lg hover:bg-white/[0.04] transition-colors"
            >
              <Search className="w-3.5 h-3.5 text-jet-500" />
              <span>Press <kbd className="text-[10px] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-jet-300">⌘K</kbd> to search</span>
            </button>
          </div>
        </motion.div>
      </motion.div>

      {/* Bottom Ambient Glow Line */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cerulean/50 to-transparent" />
    </div>
  )
}

export default HeroExperience


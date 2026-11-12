import React from 'react'
import { motion } from 'framer-motion'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showText?: boolean
  className?: string
  animated?: boolean
}

export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  showText = true,
  className = '',
  animated = true,
}) => {
  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
    xl: 'w-20 h-20',
  }[size]

  const textSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-xl',
    xl: 'text-3xl',
  }[size]

  return (
    <div className={`flex items-center space-x-3 select-none ${className}`}>
      {/* DocMind Neural Prism Mark */}
      <div
        className={`${iconSizes} rounded-2xl bg-gradient-to-br from-white/[0.08] via-white/[0.02] to-jet-950 p-1 border border-white/15 shadow-glass-lg flex items-center justify-center relative overflow-hidden group shrink-0`}
      >
        {/* Ambient Backlight Glow */}
        <div className="absolute inset-0 bg-gradient-to-tr from-cerulean/30 via-transparent to-neonrose/20 opacity-70 group-hover:opacity-100 transition-opacity duration-500 blur-sm pointer-events-none" />

        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full relative z-10 drop-shadow-[0_2px_8px_rgba(0,123,167,0.35)]"
        >
          {/* Isometric Knowledge Layers Converging into Retrieval Core */}
          <path
            d="M16 3.5L27 9.8V22.2L16 28.5L5 22.2V9.8L16 3.5Z"
            stroke="rgba(255,255,255,0.22)"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
          {/* Top Facet: Semantic Ingestion Surface */}
          <path
            d="M16 3.5L27 9.8L16 16L5 9.8L16 3.5Z"
            fill="url(#docmind-top-prism)"
            stroke="#189FD2"
            strokeWidth="1"
          />
          {/* Left Facet: Vector Space Dimension */}
          <path
            d="M16 16V28.5L5 22.2V9.8L16 16Z"
            fill="url(#docmind-left-prism)"
            stroke="rgba(0, 123, 167, 0.45)"
            strokeWidth="1"
          />
          {/* Right Facet: Cross-Encoder Grounding */}
          <path
            d="M16 16L27 9.8V22.2L16 28.5V16Z"
            fill="url(#docmind-right-prism)"
            stroke="rgba(255, 45, 149, 0.4)"
            strokeWidth="1"
          />

          {/* Core Grounding Spark */}
          <circle
            cx="16"
            cy="16"
            r="2"
            fill="#FF2D95"
            className={animated ? 'animate-pulse' : ''}
          />
          <circle
            cx="16"
            cy="16"
            r="4.5"
            stroke="#FF2D95"
            strokeWidth="0.75"
            strokeOpacity="0.4"
            className={animated ? 'animate-ping' : ''}
            style={{ animationDuration: '3s' }}
          />

          <defs>
            <linearGradient id="docmind-top-prism" x1="5" y1="3.5" x2="27" y2="16" gradientUnits="userSpaceOnUse">
              <stop stopColor="#007BA7" stopOpacity="0.85" />
              <stop offset="0.6" stopColor="#189FD2" stopOpacity="0.5" />
              <stop offset="1" stopColor="#FF2D95" stopOpacity="0.3" />
            </linearGradient>
            <linearGradient id="docmind-left-prism" x1="5" y1="9.8" x2="16" y2="28.5" gradientUnits="userSpaceOnUse">
              <stop stopColor="#0A0A0A" stopOpacity="0.95" />
              <stop offset="1" stopColor="#007BA7" stopOpacity="0.45" />
            </linearGradient>
            <linearGradient id="docmind-right-prism" x1="27" y1="9.8" x2="16" y2="28.5" gradientUnits="userSpaceOnUse">
              <stop stopColor="#121216" stopOpacity="0.95" />
              <stop offset="1" stopColor="#FF2D95" stopOpacity="0.35" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center space-x-1">
            <span className={`font-semibold tracking-tight text-white ${textSizes}`}>
              DocMind
            </span>
            <span className={`font-semibold tracking-tight bg-gradient-to-r from-cerulean-light to-white bg-clip-text text-transparent ${textSizes}`}>
              AI
            </span>
          </div>
          {size !== 'sm' && (
            <span className="text-[9px] font-mono tracking-widest uppercase text-jet-400 -mt-0.5 flex items-center gap-1.5">
              <span className="inline-block w-1 h-1 rounded-full bg-cerulean-light" />
              Intelligence Engine
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default Logo

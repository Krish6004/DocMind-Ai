import React from 'react'

export interface BadgeProps {
  children: React.ReactNode
  variant?: 'cerulean' | 'rose' | 'neutral' | 'success' | 'warning'
  size?: 'sm' | 'md'
  dot?: boolean
  className?: string
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'cerulean',
  size = 'md',
  dot = false,
  className = '',
}) => {
  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 gap-1.5',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  }[size]

  // Enforcing DocMind AI color palette: Jet Black, Cerulean Blue, Neon Rose
  const variantStyles = {
    cerulean:
      'bg-cerulean/15 text-cerulean-light border border-cerulean/30 shadow-glow-cerulean/10',
    rose:
      'bg-neonrose/15 text-neonrose-light border border-neonrose/30 shadow-glow-rose/10',
    neutral:
      'bg-white/[0.04] text-jet-300 border border-white/10',
    success:
      'bg-cerulean/20 text-cerulean-light border border-cerulean/40',
    warning:
      'bg-yellow-500/15 text-yellow-300 border border-yellow-500/30',
  }[variant]

  const dotColor = {
    cerulean: 'bg-cerulean-light shadow-glow-cerulean',
    rose: 'bg-neonrose shadow-glow-rose',
    neutral: 'bg-jet-400',
    success: 'bg-emerald-400',
    warning: 'bg-yellow-400',
  }[variant]

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full select-none transition-colors ${sizeStyles} ${variantStyles} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />}
      <span>{children}</span>
    </span>
  )
}

export default Badge

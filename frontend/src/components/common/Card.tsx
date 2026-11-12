import React from 'react'
import { motion, type HTMLMotionProps } from 'framer-motion'

export interface CardProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode
  variant?: 'default' | 'subtle' | 'cerulean' | 'rose'
  glow?: boolean
  className?: string
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  glow = false,
  className = '',
  ...props
}) => {
  const variantStyles = {
    default:
      'glass-card rounded-2xl p-6 text-jet-100',
    subtle:
      'glass-panel-subtle rounded-2xl p-5 text-jet-200 border border-white/[0.04]',
    cerulean:
      'glass-panel rounded-2xl p-6 text-jet-100 border border-cerulean/30 hover:border-cerulean/60 shadow-glow-cerulean/10 hover:shadow-glow-cerulean/25',
    rose:
      'glass-panel rounded-2xl p-6 text-jet-100 border border-neonrose/30 hover:border-neonrose/60 shadow-glow-rose/10 hover:shadow-glow-rose/25',
  }[variant]

  const glowStyle = glow
    ? variant === 'rose'
      ? 'shadow-glow-rose/30'
      : 'shadow-glow-cerulean/30'
    : ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
      className={`relative overflow-hidden ${variantStyles} ${glowStyle} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default Card

import React from 'react'

export interface SkeletonProps {
  className?: string
  variant?: 'rectangular' | 'circular' | 'rounded'
  width?: string | number
  height?: string | number
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'rounded',
  width,
  height,
}) => {
  const variantStyles = {
    rectangular: 'rounded-none',
    circular: 'rounded-full',
    rounded: 'rounded-xl',
  }[variant]

  return (
    <div
      style={{ width, height }}
      className={`animate-pulse bg-gradient-to-r from-jet-800 via-jet-750 to-jet-800 bg-[length:200%_100%] border border-white/[0.04] ${variantStyles} ${className}`}
    />
  )
}

export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`glass-panel p-6 rounded-2xl border border-white/[0.06] space-y-4 ${className}`}>
    <div className="flex items-center justify-between">
      <Skeleton className="h-5 w-1/3" />
      <Skeleton variant="circular" className="h-8 w-8" />
    </div>
    <Skeleton className="h-8 w-1/2" />
    <Skeleton className="h-4 w-4/5" />
  </div>
)

export const SkeletonMetric: React.FC = () => (
  <div className="glass-panel p-5 rounded-2xl border border-white/[0.06] space-y-3">
    <div className="flex items-center justify-between">
      <Skeleton className="h-4 w-24" />
      <Skeleton variant="circular" className="h-7 w-7" />
    </div>
    <Skeleton className="h-7 w-32" />
    <Skeleton className="h-3 w-40" />
  </div>
)

export const SkeletonTableRow: React.FC = () => (
  <div className="flex items-center space-x-4 py-4 px-5 border-b border-white/[0.04]">
    <Skeleton variant="circular" className="h-8 w-8 shrink-0" />
    <div className="flex-1 space-y-2">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-3 w-32" />
    </div>
    <Skeleton className="h-6 w-20 rounded-full" />
    <Skeleton className="h-4 w-16" />
  </div>
)

export default Skeleton

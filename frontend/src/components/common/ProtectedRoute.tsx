import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import Skeleton, { SkeletonCard } from '@/components/common/Skeleton'

const AuthLoadingSkeleton: React.FC = () => (
  <div className="min-h-screen bg-jet-950 p-8 flex items-center justify-center">
    <div className="w-full max-w-md space-y-4 glass-panel p-6 rounded-2xl border border-white/10">
      <Skeleton className="h-6 w-40 mx-auto" />
      <Skeleton className="h-4 w-60 mx-auto" />
      <div className="space-y-3 pt-4">
        <Skeleton className="h-10 w-full rounded-xl" />
        <Skeleton className="h-10 w-full rounded-xl" />
        <Skeleton className="h-10 w-full rounded-xl" />
      </div>
    </div>
  </div>
)

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <AuthLoadingSkeleton />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}

export default ProtectedRoute

import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/context/ToastContext'
import AppLayout from '@/layout/AppLayout'
import Skeleton, { SkeletonCard } from '@/components/common/Skeleton'

// Code-split pages for performance
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const ChatPage = lazy(() => import('@/pages/ChatPage'))
const DocumentsPage = lazy(() => import('@/pages/DocumentsPage'))
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'))
const EvaluationPage = lazy(() => import('@/pages/EvaluationPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 30, // 30 seconds
    },
  },
})

const PageLoader: React.FC = () => (
  <div className="space-y-6">
    <div className="glass-panel p-8 rounded-3xl space-y-4">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96" />
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  </div>
)

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route
                index
                element={
                  <Suspense fallback={<PageLoader />}>
                    <DashboardPage />
                  </Suspense>
                }
              />
              <Route
                path="chat"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ChatPage />
                  </Suspense>
                }
              />
              <Route
                path="documents"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <DocumentsPage />
                  </Suspense>
                }
              />
              <Route
                path="analytics"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <AnalyticsPage />
                  </Suspense>
                }
              />
              <Route
                path="evaluation"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <EvaluationPage />
                  </Suspense>
                }
              />
              <Route
                path="settings"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <SettingsPage />
                  </Suspense>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  )
}

export default App

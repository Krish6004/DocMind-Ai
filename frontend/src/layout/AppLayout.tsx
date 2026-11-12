import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Sidebar from './Sidebar'
import Navbar from './Navbar'
import ErrorBoundary from '@/components/common/ErrorBoundary'

export const AppLayout: React.FC = () => {
  const location = useLocation()
  const isChat = location.pathname === '/chat'

  return (
    <div className="flex min-h-screen bg-jet-950 text-jet-100 bg-ambient-pattern antialiased">
      {/* Fixed/Sticky Collapsible Sidebar */}
      <Sidebar />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />

        <main className={`flex-1 overflow-y-auto ${isChat ? 'p-3 sm:p-4' : 'p-6 lg:p-8'}`}>
          <ErrorBoundary>
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
                className={`${isChat ? 'h-full w-full' : 'max-w-7xl mx-auto w-full'}`}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </ErrorBoundary>

          {!isChat && (
            <footer className="max-w-7xl mx-auto w-full mt-12 pt-6 pb-4 border-t border-white/[0.06] relative">
              <div className="absolute top-0 left-1/4 right-1/4 h-[1px] bg-gradient-to-r from-transparent via-cerulean/50 to-transparent" />
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                <div className="flex items-center space-x-2.5 text-jet-400 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-cerulean-light shadow-[0_0_8px_rgba(56,189,248,0.8)]" />
                  <span className="text-jet-200 font-semibold tracking-tight">DocMind AI</span>
                  <span className="text-jet-600">·</span>
                  <span>Hybrid RAG Intelligence Engine</span>
                </div>

                <div className="flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] backdrop-blur-md shadow-glass-sm">
                  <span className="text-jet-400 text-[11px] tracking-wide">Created by</span>
                  <span className="font-semibold text-transparent bg-clip-text bg-gradient-to-r from-white via-cerulean-light to-neonrose tracking-tight">
                    Krish Gupta
                  </span>
                </div>
              </div>
            </footer>
          )}
        </main>
      </div>
    </div>
  )
}

export default AppLayout

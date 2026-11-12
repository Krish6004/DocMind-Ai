import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react'
import type { ToastItem, ToastType } from '@/types'

interface ToastContextValue {
  showToast: (type: ToastType, title: string, message?: string, duration?: number) => void
  success: (title: string, message?: string, duration?: number) => void
  error: (title: string, message?: string, duration?: number) => void
  info: (title: string, message?: string, duration?: number) => void
  warning: (title: string, message?: string, duration?: number) => void
  dismissToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((item) => item.id !== id))
  }, [])

  const showToast = useCallback(
    (type: ToastType, title: string, message?: string, duration = 4500) => {
      const id = Math.random().toString(36).substring(2, 9)
      const newToast: ToastItem = { id, type, title, message, duration }

      setToasts((prev) => [...prev, newToast])

      if (duration > 0) {
        setTimeout(() => {
          dismissToast(id)
        }, duration)
      }
    },
    [dismissToast]
  )

  const success = useCallback((title: string, message?: string, duration?: number) => {
    showToast('success', title, message, duration)
  }, [showToast])

  const error = useCallback((title: string, message?: string, duration?: number) => {
    showToast('error', title, message, duration)
  }, [showToast])

  const info = useCallback((title: string, message?: string, duration?: number) => {
    showToast('info', title, message, duration)
  }, [showToast])

  const warning = useCallback((title: string, message?: string, duration?: number) => {
    showToast('warning', title, message, duration)
  }, [showToast])

  return (
    <ToastContext.Provider value={{ showToast, success, error, info, warning, dismissToast }}>
      {children}
      {/* Toast Notification Container */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col space-y-3 pointer-events-none max-w-sm w-full">
        <AnimatePresence>
          {toasts.map((toast) => {
            const isError = toast.type === 'error'
            const isSuccess = toast.type === 'success'
            const isWarning = toast.type === 'warning'
            const isInfo = toast.type === 'info'

            return (
              <motion.div
                key={toast.id}
                initial={{ opacity: 0, y: 24, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 12, scale: 0.95 }}
                transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                className={`pointer-events-auto p-4 rounded-xl border glass-panel shadow-glass-lg flex items-start space-x-3 transition-colors ${
                  isError
                    ? 'border-neonrose/40 shadow-glow-rose/20'
                    : isSuccess || isInfo
                    ? 'border-cerulean/40 shadow-glow-cerulean/20'
                    : 'border-yellow-500/40 shadow-yellow-500/10'
                }`}
              >
                <div className="shrink-0 mt-0.5">
                  {isSuccess && <CheckCircle2 className="w-5 h-5 text-cerulean-light" />}
                  {isError && <AlertCircle className="w-5 h-5 text-neonrose" />}
                  {isWarning && <AlertTriangle className="w-5 h-5 text-yellow-400" />}
                  {isInfo && <Info className="w-5 h-5 text-cerulean" />}
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-semibold text-jet-100 tracking-tight">{toast.title}</h4>
                  {toast.message && (
                    <p className="mt-1 text-xs text-jet-300 leading-relaxed break-words">{toast.message}</p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => dismissToast(toast.id)}
                  className="shrink-0 text-jet-400 hover:text-jet-100 p-1 rounded-lg hover:bg-white/5 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export default ToastContext

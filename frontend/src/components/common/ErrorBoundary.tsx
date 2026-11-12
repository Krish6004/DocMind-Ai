import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import Button from './Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('DocMind UI Caught Unhandled Error:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md w-full glass-panel p-8 rounded-2xl border border-neonrose/30 shadow-glow-rose/20 text-center">
            <div className="w-14 h-14 rounded-2xl bg-neonrose/15 border border-neonrose/40 flex items-center justify-center mx-auto mb-5 text-neonrose shadow-glow-rose/30">
              <AlertTriangle className="w-7 h-7" />
            </div>

            <h2 className="text-xl font-bold text-jet-100 tracking-tight">Something went wrong</h2>
            <p className="text-xs text-jet-300 mt-2 mb-6 leading-relaxed">
              An unexpected client error occurred in the DocMind AI interface.
            </p>

            {this.state.error && (
              <div className="p-3 bg-jet-950/80 rounded-xl border border-white/5 text-left mb-6 overflow-x-auto">
                <code className="text-xs font-mono text-neonrose-light">
                  {this.state.error.message || 'Unknown Exception'}
                </code>
              </div>
            )}

            <Button
              variant="rose"
              size="md"
              leftIcon={<RefreshCw className="w-4 h-4" />}
              onClick={this.handleReset}
              className="w-full"
            >
              Reload Application
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

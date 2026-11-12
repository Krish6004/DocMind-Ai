import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import authService from '@/services/authService'
import { ACCESS_TOKEN_KEY } from '@/services/apiClient'
import type { AuthUser } from '@/types'

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function clearUserLocalCaches() {
  try {
    localStorage.removeItem('docmind_chat_sessions_v1')
    Object.keys(localStorage).forEach((k) => {
      if (k.startsWith('docmind_messages_session_')) {
        localStorage.removeItem(k)
      }
    })
  } catch {
    // ignore storage errors
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const restoreSession = useCallback(async () => {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }
    try {
      const me = await authService.getMe()
      setUser(me)
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    restoreSession()
  }, [restoreSession])

  useEffect(() => {
    const onExpired = () => {
      setUser(null)
      clearUserLocalCaches()
      queryClient.clear()
    }
    window.addEventListener('docmind:auth-expired', onExpired)
    return () => window.removeEventListener('docmind:auth-expired', onExpired)
  }, [queryClient])

  const login = useCallback(
    async (email: string, password: string) => {
      clearUserLocalCaches()
      queryClient.clear()
      const data = await authService.login(email, password)
      setUser(data.user)
    },
    [queryClient]
  )

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      clearUserLocalCaches()
      queryClient.clear()
      const data = await authService.register(name, email, password)
      setUser(data.user)
    },
    [queryClient]
  )

  const logout = useCallback(async () => {
    await authService.logout()
    setUser(null)
    clearUserLocalCaches()
    queryClient.clear()
  }, [queryClient])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: Boolean(user),
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

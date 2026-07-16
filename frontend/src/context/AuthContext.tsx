/**
 * AuthContext — provides current user and login/logout actions
 * to the entire React component tree.
 */

import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import {
  login as apiLogin,
  fetchCurrentUser,
  setToken,
  clearToken,
  getToken,
  getStoredUser,
  type User,
} from '../api/client'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(getStoredUser)
  const [isLoading, setIsLoading] = useState(false)

  // Re-validate token on mount
  useEffect(() => {
    const token = getToken()
    if (token && !user) {
      setIsLoading(true)
      fetchCurrentUser()
        .then((u) => {
          setUser(u)
          localStorage.setItem('apex_user', JSON.stringify(u))
        })
        .catch(() => {
          clearToken()
          setUser(null)
        })
        .finally(() => setIsLoading(false))
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function login(email: string, password: string) {
    setIsLoading(true)
    try {
      const tokenResp = await apiLogin(email, password)
      setToken(tokenResp.access_token)
      const me = await fetchCurrentUser()
      setUser(me)
      localStorage.setItem('apex_user', JSON.stringify(me))
    } finally {
      setIsLoading(false)
    }
  }

  function logout() {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, isLoading, isAuthenticated: !!user, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

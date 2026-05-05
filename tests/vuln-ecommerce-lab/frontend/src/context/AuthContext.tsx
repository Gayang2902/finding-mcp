import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, LoginRequest, RegisterRequest, Role } from '@/types'
import { authService } from '@/services/authService'

interface AuthContextValue {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  isAdmin: boolean
  isSeller: boolean
  login: (email: string, password: string) => Promise<void>
  register: (request: RegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user && !!token
  const isAdmin = user?.role === Role.ADMIN
  const isSeller = user?.role === Role.SELLER || user?.role === Role.ADMIN

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      setToken(storedToken)
      authService.getProfile()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setToken(null)
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password } as LoginRequest)
    localStorage.setItem('token', response.token)
    setToken(response.token)
    setUser(response.user)
  }

  const register = async (request: RegisterRequest) => {
    const response = await authService.register(request)
    localStorage.setItem('token', response.token)
    setToken(response.token)
    setUser(response.user)
  }

  const logout = () => {
    authService.logout()
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }

  const refreshUser = async () => {
    const updated = await authService.getProfile()
    setUser(updated)
  }

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, isLoading, isAdmin, isSeller, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

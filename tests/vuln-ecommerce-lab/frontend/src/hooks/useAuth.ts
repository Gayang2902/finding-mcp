import { useState } from 'react'
import { User, Role } from '../types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  logout: () => void
}

// Stub hook — replace with real context-based implementation
export function useAuth(): AuthState {
  const [user] = useState<User | null>(null)

  return {
    user,
    isAuthenticated: user !== null,
    logout: () => {
      localStorage.removeItem('token')
      window.location.href = '/login'
    },
  }
}

export { Role }

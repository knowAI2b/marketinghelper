import { createContext, useCallback, useContext, useState } from "react"
import {
  clearStoredAuth,
  getStoredToken,
  getStoredUsername,
  setStoredAuth,
} from "../stores/authStore"

interface AuthState {
  token: string | null
  username: string | null
}

interface AuthContextValue extends AuthState {
  isLoggedIn: boolean
  setAuth: (token: string, username: string) => void
  clearAuth: () => void
  loadStored: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(() => ({
    token: getStoredToken(),
    username: getStoredUsername(),
  }))

  const loadStored = useCallback(() => {
    setState({
      token: getStoredToken(),
      username: getStoredUsername(),
    })
  }, [])

  const setAuth = useCallback((token: string, username: string) => {
    setStoredAuth(token, username)
    setState({ token, username })
  }, [])

  const clearAuth = useCallback(() => {
    clearStoredAuth()
    setState({ token: null, username: null })
  }, [])

  const value: AuthContextValue = {
    ...state,
    isLoggedIn: !!state.token,
    setAuth,
    clearAuth,
    loadStored,
  }

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}

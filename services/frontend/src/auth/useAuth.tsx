import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import keycloak from './keycloak'

interface AuthContextType {
  authenticated: boolean
  token: string | undefined
  user: { name: string; email: string } | null
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  authenticated: false,
  token: undefined,
  user: null,
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false)
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    keycloak
      .init({ onLoad: 'login-required', checkLoginIframe: false })
      .then((auth) => {
        setAuthenticated(auth)
        setInitialized(true)
      })
      .catch((err) => {
        console.error('Keycloak init failed', err)
        setInitialized(true)
      })

    // Token refresh interval
    const interval = setInterval(() => {
      keycloak.updateToken(30).catch(() => keycloak.login())
    }, 10000)

    return () => clearInterval(interval)
  }, [])

  const logout = useCallback(() => {
    keycloak.logout({ redirectUri: window.location.origin })
  }, [])

  const user = keycloak.tokenParsed
    ? {
        name: keycloak.tokenParsed.preferred_username || keycloak.tokenParsed.name || 'User',
        email: keycloak.tokenParsed.email || '',
      }
    : null

  if (!initialized) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950 text-slate-400">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
          Connecting to identity provider...
        </div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ authenticated, token: keycloak.token, user, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

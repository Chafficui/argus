import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import keycloak from './keycloak'

interface AuthContextType {
  authenticated: boolean
  initialized: boolean
  token: string | undefined
  user: { name: string; email: string } | null
  roles: string[]
  login: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  authenticated: false,
  initialized: false,
  token: undefined,
  user: null,
  roles: [],
  login: () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false)
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    keycloak
      .init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        checkLoginIframe: false,
        messageReceiveTimeout: 1000,
      })
      .then((auth) => {
        setAuthenticated(auth)
        setInitialized(true)
      })
      .catch((err) => {
        console.error('Keycloak init failed', err)
        setInitialized(true)
      })
  }, [])

  useEffect(() => {
    if (!authenticated) return
    const interval = setInterval(() => {
      keycloak.updateToken(30).catch(() => keycloak.login())
    }, 10000)
    return () => clearInterval(interval)
  }, [authenticated])

  const login = useCallback(() => {
    keycloak.login()
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

  const roles: string[] = keycloak.tokenParsed?.realm_access?.roles || []

  return (
    <AuthContext.Provider value={{ authenticated, initialized, token: keycloak.token, user, roles, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext)
}

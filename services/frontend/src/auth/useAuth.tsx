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
      <div
        className="flex items-center justify-center h-screen"
        style={{ background: 'var(--bg-void)', color: 'var(--fg-muted)' }}
      >
        <div className="text-center">
          <div
            className="pulse-core mx-auto"
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: 'var(--core-500)',
              marginBottom: 16,
            }}
          />
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 600, letterSpacing: '0.18em', textTransform: 'uppercase' }}>
            Connecting...
          </div>
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

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext)
}

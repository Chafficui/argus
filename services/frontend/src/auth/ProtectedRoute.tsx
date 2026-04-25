import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { authenticated, initialized } = useAuth()

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

  if (!authenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

import { useAuth } from '../auth/useAuth'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { authenticated } = useAuth()

  if (!authenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950 text-slate-400">
        Redirecting to login...
      </div>
    )
  }

  return <>{children}</>
}

import { useAuth } from '../auth/useAuth'
import { Eyebrow } from '../components/Brand'
import { IconExternal } from '../components/Icons'

const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL || `${window.location.origin}/auth`

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        background: 'var(--bg-surface-2)',
        border: '1px solid var(--line-default)',
        borderRadius: 'var(--radius-xl)',
        padding: '24px 28px',
      }}
    >
      {children}
    </div>
  )
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        fontFamily: 'var(--font-display)',
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.18em',
        textTransform: 'uppercase' as const,
        color: 'var(--fg-muted)',
      }}
    >
      {children}
    </span>
  )
}

function ExternalLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center"
      style={{
        gap: 10,
        padding: '12px 16px',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--line-default)',
        background: 'var(--bg-surface-1)',
        color: 'var(--fg-body)',
        fontFamily: 'var(--font-sans)',
        fontSize: 13,
        fontWeight: 500,
        textDecoration: 'none',
        transition: 'all 150ms',
      }}
    >
      <span className="flex-1">{children}</span>
      <IconExternal size={14} style={{ color: 'var(--fg-subtle)' }} />
    </a>
  )
}

export default function Settings() {
  const { user, roles } = useAuth()
  const isAdmin = roles.includes('admin')

  return (
    <div style={{ padding: '28px 36px 40px', maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ marginBottom: 28 }}>
        <Eyebrow>Settings</Eyebrow>
      </div>

      <div className="flex flex-col" style={{ gap: 20 }}>
        {/* Profile */}
        <Card>
          <div style={{ marginBottom: 20 }}>
            <Label>Profile</Label>
          </div>
          <div className="flex items-center" style={{ gap: 16, marginBottom: 20 }}>
            <div
              className="flex items-center justify-center shrink-0"
              style={{
                width: 48,
                height: 48,
                borderRadius: 'var(--radius-lg)',
                background: 'var(--signal-500-a10)',
                border: '1px solid var(--signal-500-a20)',
                color: 'var(--signal-300)',
                fontFamily: 'var(--font-display)',
                fontSize: 20,
                fontWeight: 600,
              }}
            >
              {user?.name?.[0]?.toUpperCase() || '?'}
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: 15, fontWeight: 600, color: 'var(--fg-bright)' }}>
                {user?.name}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--fg-muted)', marginTop: 2 }}>
                {user?.email}
              </div>
            </div>
          </div>
          <div className="flex flex-col" style={{ gap: 12 }}>
            <div className="flex items-center" style={{ gap: 16 }}>
              <Label>Roles</Label>
              <div className="flex" style={{ gap: 6 }}>
                {roles.map((role) => (
                  <span
                    key={role}
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--signal-500-a10)',
                      color: 'var(--signal-400)',
                      border: '1px solid var(--signal-500-a20)',
                    }}
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* Admin */}
        {isAdmin && (
          <Card>
            <div style={{ marginBottom: 20 }}>
              <Label>Administration</Label>
            </div>
            <div className="flex flex-col" style={{ gap: 10 }}>
              <ExternalLink href={`${keycloakUrl}/admin/argus/console`}>
                Keycloak Admin Console
              </ExternalLink>
              <ExternalLink href="/grafana">
                Grafana Dashboard
              </ExternalLink>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}

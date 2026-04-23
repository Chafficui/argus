import { useState, useEffect } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { Brand } from './Brand'
import { IconSearch, IconSources, IconChat, IconSettings } from './Icons'
import api from '../api/client'

const navItems = [
  { to: '/search', label: 'Search', Icon: IconSearch },
  { to: '/', label: 'Sources', Icon: IconSources, showCount: true },
  { to: '/chat', label: 'Chat', Icon: IconChat },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const [sourceCount, setSourceCount] = useState<number | null>(null)
  const [liveCrawls, setLiveCrawls] = useState(0)

  useEffect(() => {
    api.get('/api/sources/').then((res) => {
      setSourceCount(res.data.length)
      setLiveCrawls(res.data.filter((s: { is_active: boolean }) => s.is_active).length)
    }).catch(() => {})
  }, [])

  return (
    <div className="flex h-screen" style={{ background: 'var(--bg-void)', color: 'var(--fg-body)' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: 240,
          flexShrink: 0,
          background: 'var(--bg-surface-1)',
          borderRight: '1px solid var(--line-default)',
          display: 'flex',
          flexDirection: 'column',
          padding: '22px 14px 14px',
          height: '100vh',
          boxSizing: 'border-box',
        }}
      >
        {/* Brand */}
        <div style={{ padding: '0 6px 22px', borderBottom: '1px solid var(--line-hairline)', marginBottom: 14 }}>
          <Brand size={32} />
        </div>

        {/* Section label */}
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.22em',
            textTransform: 'uppercase',
            color: 'var(--fg-faint)',
            padding: '0 14px 8px',
          }}
        >
          Workspace
        </div>

        {/* Nav */}
        <nav className="flex flex-col" style={{ gap: 2 }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className="group"
            >
              {({ isActive }) => (
                <div
                  className="relative flex items-center"
                  style={{
                    gap: 12,
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    fontFamily: 'var(--font-sans)',
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all 150ms cubic-bezier(0.2, 0.8, 0.2, 1)',
                    background: isActive ? 'var(--signal-500-a10)' : 'transparent',
                    color: isActive ? 'var(--signal-300)' : 'var(--fg-muted)',
                  }}
                >
                  {isActive && (
                    <div
                      style={{
                        position: 'absolute',
                        left: 0,
                        top: 8,
                        bottom: 8,
                        width: 2,
                        background: 'var(--signal-500)',
                        borderRadius: 1,
                      }}
                    />
                  )}
                  <item.Icon size={16} />
                  <span>{item.label}</span>
                  {item.showCount && sourceCount != null && (
                    <span
                      className="ml-auto"
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: 11,
                        color: isActive ? 'var(--signal-400)' : 'var(--fg-subtle)',
                      }}
                    >
                      {String(sourceCount).padStart(2, '0')}
                    </span>
                  )}
                </div>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex-1" />

        {/* Crawl status */}
        <div
          style={{
            border: '1px solid var(--line-default)',
            borderRadius: 'var(--radius-lg)',
            padding: '12px 14px',
            background: 'var(--bg-surface-2)',
            marginBottom: 12,
          }}
        >
          <div className="flex items-center" style={{ gap: 8, marginBottom: 8 }}>
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: liveCrawls > 0 ? 'var(--status-ok)' : 'var(--fg-subtle)',
              }}
            />
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 10,
                fontWeight: 600,
                letterSpacing: '0.18em',
                textTransform: 'uppercase',
                color: 'var(--fg-muted)',
              }}
            >
              Crawler
            </span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)', lineHeight: 1.6 }}>
            <div>{String(liveCrawls).padStart(2, '0')} sources active</div>
            <div style={{ color: 'var(--fg-subtle)' }}>
              {sourceCount != null ? `${String(sourceCount).padStart(2, '0')} monitored` : '...'}
            </div>
          </div>
        </div>

        {/* Settings */}
        <div
          className="flex items-center"
          style={{
            gap: 12,
            padding: '10px 14px',
            borderRadius: 'var(--radius-md)',
            fontFamily: 'var(--font-sans)',
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--fg-muted)',
            cursor: 'pointer',
            transition: 'all 150ms',
          }}
        >
          <IconSettings size={16} />
          <span>Settings</span>
        </div>

        {/* User */}
        <div style={{ padding: '12px 8px 0', borderTop: '1px solid var(--line-hairline)', marginTop: 8 }}>
          <div className="flex items-center" style={{ gap: 10 }}>
            <div
              className="flex items-center justify-center shrink-0"
              style={{
                width: 28,
                height: 28,
                borderRadius: 'var(--radius-md)',
                background: 'var(--signal-500-a10)',
                border: '1px solid var(--signal-500-a20)',
                color: 'var(--signal-300)',
                fontFamily: 'var(--font-display)',
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              {user?.name?.[0]?.toUpperCase() || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate" style={{ fontSize: 12, fontWeight: 500, color: 'var(--fg-bright)', margin: 0 }}>
                {user?.name}
              </p>
            </div>
            <button
              onClick={logout}
              style={{
                fontSize: 10,
                fontFamily: 'var(--font-display)',
                fontWeight: 600,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: 'var(--fg-subtle)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                transition: 'color 150ms',
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto" style={{ background: 'var(--bg-void)' }}>
        <Outlet />
      </main>
    </div>
  )
}

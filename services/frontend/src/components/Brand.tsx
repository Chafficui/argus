interface BrandProps {
  size?: number
  showWordmark?: boolean
  compact?: boolean
}

export function Brand({ size = 32, showWordmark = true, compact = false }: BrandProps) {
  return (
    <div className="flex items-center" style={{ gap: compact ? 8 : 10 }}>
      <img
        src="/argus-logo.png"
        alt="Argus"
        width={size}
        height={size}
        className="block"
        style={{ filter: 'drop-shadow(0 0 10px rgba(34,211,238,0.25))' }}
      />
      {showWordmark && (
        <div className="flex flex-col" style={{ lineHeight: 1 }}>
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: compact ? 14 : 16,
              fontWeight: 700,
              letterSpacing: '0.18em',
              color: 'var(--fg-bright)',
            }}
          >
            ARG<span style={{ color: 'var(--signal-500)' }}>U</span>S
          </span>
          {!compact && (
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 9,
                fontWeight: 600,
                letterSpacing: '0.22em',
                color: 'var(--fg-subtle)',
                marginTop: 4,
                textTransform: 'uppercase',
              }}
            >
              Observatory
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export function CornerBrackets({
  color = 'var(--signal-500)',
  opacity = 0.5,
  size = 12,
}: {
  color?: string
  opacity?: number
  size?: number
}) {
  const base: React.CSSProperties = { position: 'absolute', width: size, height: size, pointerEvents: 'none' }
  const line: React.CSSProperties = { position: 'absolute', background: color, opacity }

  return (
    <>
      <div style={{ ...base, top: -1, left: -1 }}>
        <div style={{ ...line, left: 0, top: 0, width: size, height: 1 }} />
        <div style={{ ...line, left: 0, top: 0, width: 1, height: size }} />
      </div>
      <div style={{ ...base, top: -1, right: -1 }}>
        <div style={{ ...line, right: 0, top: 0, width: size, height: 1 }} />
        <div style={{ ...line, right: 0, top: 0, width: 1, height: size }} />
      </div>
      <div style={{ ...base, bottom: -1, left: -1 }}>
        <div style={{ ...line, left: 0, bottom: 0, width: size, height: 1 }} />
        <div style={{ ...line, left: 0, bottom: 0, width: 1, height: size }} />
      </div>
      <div style={{ ...base, bottom: -1, right: -1 }}>
        <div style={{ ...line, right: 0, bottom: 0, width: size, height: 1 }} />
        <div style={{ ...line, right: 0, bottom: 0, width: 1, height: size }} />
      </div>
    </>
  )
}

export function Eyebrow({
  children,
  color,
  count,
}: {
  children: React.ReactNode
  color?: string
  count?: number
}) {
  return (
    <div className="flex items-center" style={{ gap: 8 }}>
      <span
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          color: color || 'var(--fg-muted)',
        }}
      >
        {children}
      </span>
      {count != null && (
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--signal-400)',
          }}
        >
          · {String(count).padStart(2, '0')}
        </span>
      )}
    </div>
  )
}

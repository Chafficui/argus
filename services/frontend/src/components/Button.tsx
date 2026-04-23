interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  icon?: React.ReactNode
  children: React.ReactNode
  onClick?: () => void
  type?: 'button' | 'submit'
  disabled?: boolean
  className?: string
}

const variantStyles: Record<string, React.CSSProperties> = {
  primary: {
    background: 'linear-gradient(180deg, #2FBBD5, #0E7490)',
    color: '#031218',
    borderColor: 'rgba(34,211,238, 0.6)',
    boxShadow: 'var(--glow-core)',
  },
  secondary: {
    background: 'var(--signal-500-a10)',
    color: 'var(--signal-300)',
    borderColor: 'var(--signal-500-a30)',
  },
  ghost: {
    background: 'transparent',
    color: 'var(--fg-muted)',
    borderColor: 'transparent',
  },
  danger: {
    background: 'var(--status-alert-a10)',
    color: 'var(--status-alert)',
    borderColor: 'rgba(248,113,113,0.3)',
  },
}

const sizeStyles: Record<string, React.CSSProperties> = {
  sm: { padding: '5px 10px', fontSize: 12 },
  md: {},
  lg: { padding: '10px 18px', fontSize: 14 },
}

export default function Button({
  variant = 'secondary',
  size = 'md',
  icon,
  children,
  onClick,
  type = 'button',
  disabled,
  className = '',
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        padding: '8px 14px',
        fontFamily: 'var(--font-sans)',
        fontSize: 13,
        fontWeight: 600,
        letterSpacing: '0.02em',
        borderRadius: 'var(--radius-md)',
        border: '1px solid transparent',
        cursor: disabled ? 'not-allowed' : 'pointer',
        userSelect: 'none',
        whiteSpace: 'nowrap',
        transition: 'all 150ms cubic-bezier(0.2, 0.8, 0.2, 1)',
        opacity: disabled ? 0.5 : 1,
        ...variantStyles[variant],
        ...sizeStyles[size],
      }}
    >
      {icon}
      {children}
    </button>
  )
}

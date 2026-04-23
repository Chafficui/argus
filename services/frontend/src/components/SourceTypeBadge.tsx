const TypeMeta: Record<string, { label: string; color: string; bg: string; border: string }> = {
  website: {
    label: 'Website',
    color: 'var(--type-website)',
    bg: 'rgba(96,165,250,0.1)',
    border: 'rgba(96,165,250,0.25)',
  },
  rss: {
    label: 'RSS',
    color: 'var(--type-rss)',
    bg: 'rgba(251,146,60,0.1)',
    border: 'rgba(251,146,60,0.25)',
  },
  serp: {
    label: 'SERP',
    color: 'var(--type-serp)',
    bg: 'rgba(192,132,252,0.1)',
    border: 'rgba(192,132,252,0.25)',
  },
}

export { TypeMeta }

export default function SourceTypeBadge({ type, size = 'md' }: { type: string; size?: 'sm' | 'md' }) {
  const meta = TypeMeta[type]
  if (!meta) return null
  const sm = size === 'sm'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: sm ? '2px 8px' : '3px 10px',
        borderRadius: 'var(--radius-pill)',
        background: meta.bg,
        color: meta.color,
        border: `1px solid ${meta.border}`,
        fontFamily: 'var(--font-display)',
        fontSize: sm ? 10 : 11,
        fontWeight: 600,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
      }}
    >
      {meta.label}
    </span>
  )
}

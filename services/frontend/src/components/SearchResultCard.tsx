import { useState } from 'react'
import SourceTypeBadge from './SourceTypeBadge'
import { CornerBrackets } from './Brand'
import { IconExternal } from './Icons'

interface SearchResult {
  chunk_id: string
  document_id: string
  source_id: string
  text: string
  title: string
  url: string
  chunk_index: number
  score: number
  source_name: string | null
}

const TRUNCATE_LEN = 300

export default function SearchResultCard({ result }: { result: SearchResult }) {
  const [expanded, setExpanded] = useState(false)
  const [hover, setHover] = useState(false)
  const scorePct = Math.round(result.score * 100)

  const needsTruncate = result.text.length > TRUNCATE_LEN
  const displayText = expanded || !needsTruncate ? result.text : result.text.slice(0, TRUNCATE_LEN) + '...'

  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative',
        background: hover ? 'var(--bg-surface-hover)' : 'var(--bg-surface-2)',
        border: `1px solid ${hover ? 'var(--line-strong)' : 'var(--line-default)'}`,
        borderRadius: 'var(--radius-xl)',
        padding: '18px 20px',
        transition: 'all 150ms cubic-bezier(0.2, 0.8, 0.2, 1)',
        overflow: 'hidden',
      }}
    >
      {hover && <CornerBrackets opacity={0.4} />}

      {/* Score badge — top right */}
      <div
        style={{
          position: 'absolute',
          top: 14,
          right: 16,
          padding: '3px 10px',
          borderRadius: 'var(--radius-pill)',
          background: scorePct >= 80 ? 'var(--signal-500-a20)' : scorePct >= 60 ? 'var(--signal-500-a10)' : 'rgba(76,130,255,0.06)',
          color: scorePct >= 80 ? 'var(--signal-300)' : scorePct >= 60 ? 'var(--signal-400)' : 'var(--fg-muted)',
          border: `1px solid ${scorePct >= 80 ? 'var(--signal-500-a30)' : 'var(--line-default)'}`,
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          fontWeight: 600,
        }}
      >
        {scorePct}%
      </div>

      {/* Title */}
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 15,
          fontWeight: 600,
          color: 'var(--fg-bright)',
          letterSpacing: '0.02em',
          paddingRight: 60,
        }}
      >
        {result.title || 'Untitled document'}
      </div>

      {/* Source + type badge */}
      <div className="flex items-center flex-wrap" style={{ gap: 8, marginTop: 8 }}>
        {result.source_name && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)' }}>
            {result.source_name}
          </span>
        )}
        <SourceTypeBadge type="website" size="sm" />
      </div>

      {/* Text snippet */}
      <div
        style={{
          marginTop: 14,
          fontFamily: 'var(--font-sans)',
          fontSize: 13,
          lineHeight: 1.65,
          color: 'var(--fg-body)',
        }}
      >
        {displayText}
      </div>

      {needsTruncate && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            marginTop: 8,
            fontFamily: 'var(--font-display)',
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: 'var(--signal-400)',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}

      {/* URL link */}
      <div className="flex items-center" style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--line-hairline)', gap: 6 }}>
        <IconExternal size={12} style={{ color: 'var(--fg-subtle)', flexShrink: 0 }} />
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--signal-400)',
            textDecoration: 'none',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            transition: 'color 150ms',
          }}
        >
          {result.url}
        </a>
      </div>
    </div>
  )
}

import { useState } from 'react'
import api from '../api/client'
import { CornerBrackets } from './Brand'
import SourceTypeBadge from './SourceTypeBadge'
import { IconRefresh, IconExternal, IconTrash } from './Icons'

interface CrawlJob {
  id: string
  status: string
  documents_found: number
  documents_indexed: number
  duration_seconds: number
  started_at: string
  error_message?: string | null
}

interface Source {
  id: string
  name: string
  url: string
  source_type: string
  search_query?: string | null
  is_active: boolean
  created_at: string
  last_crawled_at?: string | null
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function IconBtn({
  children,
  onClick,
  title,
  danger,
}: {
  children: React.ReactNode
  onClick?: () => void
  title: string
  danger?: boolean
}) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      title={title}
      className={`inline-flex items-center justify-center transition-all duration-150 ${
        danger
          ? 'hover:bg-[rgba(248,113,113,0.1)] hover:text-[var(--status-alert)] hover:border-[rgba(248,113,113,0.3)]'
          : 'hover:bg-[var(--signal-500-a10)] hover:text-[var(--signal-300)] hover:border-[var(--signal-500-a30)]'
      }`}
      style={{
        width: 26,
        height: 26,
        background: 'transparent',
        color: 'var(--fg-muted)',
        border: '1px solid transparent',
        borderRadius: 'var(--radius-sm)',
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  )
}

export default function SourceCard({
  source,
  onDelete,
}: {
  source: Source
  onDelete: (id: string) => void
}) {
  const [hover, setHover] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [crawlJobs, setCrawlJobs] = useState<CrawlJob[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  const loadCrawlHistory = async () => {
    if (showHistory) {
      setShowHistory(false)
      return
    }
    setLoadingHistory(true)
    try {
      const res = await api.get(`/api/sources/${source.id}/crawl-jobs`)
      setCrawlJobs(res.data.slice(0, 5))
      setShowHistory(true)
    } catch (err) {
      console.error('Failed to load crawl history', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleDelete = async () => {
    try {
      await api.delete(`/api/sources/${source.id}`)
      onDelete(source.id)
    } catch (err) {
      console.error('Failed to delete source', err)
    }
  }

  const handleRefresh = async () => {
    try {
      await api.post(`/api/sources/${source.id}/crawl`)
    } catch (err) {
      console.error('Failed to trigger crawl', err)
    }
  }

  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative',
        background: hover ? 'var(--bg-surface-hover)' : 'var(--bg-surface-2)',
        border: `1px solid ${hover ? 'var(--line-strong)' : 'var(--line-default)'}`,
        borderRadius: 'var(--radius-xl)',
        padding: '18px 20px 20px',
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gap: '14px 20px',
        transition: 'all 150ms cubic-bezier(0.2, 0.8, 0.2, 1)',
        overflow: 'hidden',
      }}
    >
      {hover && <CornerBrackets opacity={0.6} />}

      {/* Left column */}
      <div>
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 16,
            fontWeight: 600,
            color: 'var(--fg-bright)',
            letterSpacing: '0.02em',
          }}
        >
          {source.name}
        </div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--fg-muted)',
            marginTop: 4,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {source.url}
        </div>

        <div className="flex items-center flex-wrap" style={{ gap: 8, marginTop: 12 }}>
          <SourceTypeBadge type={source.source_type} size="sm" />
          <span
            className={source.is_active ? 'pulse-core' : ''}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '2px 8px',
              borderRadius: 'var(--radius-pill)',
              background: source.is_active ? 'rgba(34,211,238,0.08)' : 'var(--status-ok-a10)',
              color: source.is_active ? 'var(--core-400)' : 'var(--status-ok)',
              border: `1px solid ${source.is_active ? 'rgba(34,211,238,0.25)' : 'rgba(52,211,153,0.25)'}`,
              fontFamily: 'var(--font-display)',
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
            }}
          >
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor' }} />
            {source.is_active ? 'Live' : 'Synced'}
          </span>
          {source.search_query && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)' }}>
              <span style={{ color: 'var(--type-serp)', marginRight: 4 }}>?</span>
              {source.search_query}
            </span>
          )}
        </div>
      </div>

      {/* Right column — stats */}
      <div className="flex flex-col items-end" style={{ gap: 4 }}>
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 26,
            fontWeight: 600,
            color: 'var(--fg-bright)',
            letterSpacing: '0.02em',
            lineHeight: 1,
          }}
        >
          —
        </div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--fg-subtle)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          docs indexed
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)', marginTop: 4 }}>
          {source.last_crawled_at ? timeAgo(source.last_crawled_at) : 'never'}
        </div>
      </div>

      {/* Hover actions */}
      {hover && (
        <div
          className="flex"
          style={{ position: 'absolute', top: 14, right: 16, gap: 4 }}
        >
          <IconBtn title="Refresh now" onClick={handleRefresh}>
            <IconRefresh size={14} />
          </IconBtn>
          <IconBtn title="Open source" onClick={() => window.open(source.url, '_blank')}>
            <IconExternal size={14} />
          </IconBtn>
          <IconBtn title="Remove" danger onClick={handleDelete}>
            <IconTrash size={14} />
          </IconBtn>
        </div>
      )}

      {/* Live scan-sweep bar */}
      {source.is_active && (
        <div
          style={{
            position: 'absolute',
            left: 20,
            right: 20,
            bottom: 10,
            height: 1,
            background: 'var(--line-hairline)',
            overflow: 'hidden',
            gridColumn: '1 / -1',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '40%',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, var(--core-500), transparent)',
              animation: 'scan-sweep 2.4s ease-in-out infinite',
            }}
          />
        </div>
      )}

      {/* Crawl history toggle */}
      <div
        className="flex items-center justify-between"
        style={{
          gridColumn: '1 / -1',
          paddingTop: 14,
          borderTop: '1px solid var(--line-hairline)',
        }}
      >
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)' }}>
          Added {timeAgo(source.created_at)}
        </div>
        <button
          onClick={loadCrawlHistory}
          disabled={loadingHistory}
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: 'var(--signal-400)',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            transition: 'color 150ms',
          }}
        >
          {loadingHistory ? 'Loading...' : showHistory ? 'Hide history' : 'Crawl history'}
        </button>
      </div>

      {/* Crawl history rows */}
      {showHistory && (
        <div className="flex flex-col" style={{ gridColumn: '1 / -1', gap: 4 }}>
          {crawlJobs.length === 0 ? (
            <p style={{ fontSize: 11, color: 'var(--fg-faint)' }}>No crawl jobs yet</p>
          ) : (
            crawlJobs.map((job) => (
              <div
                key={job.id}
                className="flex items-center"
                style={{
                  gap: 12,
                  padding: '8px 12px',
                  background: 'var(--bg-surface-3)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--line-hairline)',
                }}
              >
                <span
                  style={{
                    width: 5,
                    height: 5,
                    borderRadius: '50%',
                    flexShrink: 0,
                    background: job.status === 'success' ? 'var(--status-ok)' : 'var(--status-alert)',
                  }}
                />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)' }}>
                  {timeAgo(job.started_at)}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)' }}>
                  {job.documents_indexed}/{job.documents_found} docs
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-faint)' }}>
                  {job.duration_seconds.toFixed(1)}s
                </span>
                {job.error_message && (
                  <span className="truncate" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--status-alert)' }}>
                    {job.error_message}
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

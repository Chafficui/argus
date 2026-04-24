import { useState } from 'react'
import api from '../api/client'
import SourceTypeBadge from './SourceTypeBadge'
import { IconExternal, IconTrash, IconClock } from './Icons'

interface CrawlJob {
  id: string
  status: string
  documents_found: number
  documents_indexed: number
  duration_seconds: number | null
  started_at: string | null
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
  document_count: number
  crawl_interval_minutes: number
}

function formatInterval(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  if (minutes % 1440 === 0) return `${minutes / 1440}d`
  if (minutes % 60 === 0) return `${minutes / 60}h`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h ${m}m`
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

export default function SourceCard({
  source,
  onDelete,
}: {
  source: Source
  onDelete: (id: string) => void
}) {
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

  return (
    <div
      style={{
        background: 'var(--bg-surface-2)',
        border: '1px solid var(--line-default)',
        borderRadius: 'var(--radius-xl)',
        padding: '18px 20px 14px',
        transition: 'border-color 150ms',
      }}
    >
      {/* Top row: info left, stats right */}
      <div className="flex justify-between" style={{ gap: 20 }}>
        {/* Left: name, url, badges */}
        <div style={{ minWidth: 0, flex: 1 }}>
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

          <div className="flex items-center flex-wrap" style={{ gap: 8, marginTop: 10 }}>
            <SourceTypeBadge type={source.source_type} size="sm" />
            <span
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

        {/* Right: doc count + last crawled */}
        <div className="flex flex-col items-end shrink-0" style={{ gap: 4 }}>
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
            {source.document_count}
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
      </div>

      {/* Footer row: metadata left, actions right */}
      <div
        className="flex items-center justify-between"
        style={{
          marginTop: 14,
          paddingTop: 10,
          borderTop: '1px solid var(--line-hairline)',
        }}
      >
        <div className="flex items-center" style={{ gap: 12 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)' }}>
            Added {timeAgo(source.created_at)}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)' }}>
            every {formatInterval(source.crawl_interval_minutes)}
          </span>
          <button
            onClick={loadCrawlHistory}
            disabled={loadingHistory}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 500,
              color: 'var(--signal-400)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
            }}
          >
            <IconClock size={11} />
            {loadingHistory ? 'Loading...' : showHistory ? 'Hide history' : 'Crawl history'}
          </button>
        </div>

        <div className="flex items-center" style={{ gap: 4 }}>
          <button
            onClick={() => window.open(source.url, '_blank')}
            title="Open source"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 26,
              height: 26,
              background: 'transparent',
              color: 'var(--fg-muted)',
              border: '1px solid transparent',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
            }}
          >
            <IconExternal size={13} />
          </button>
          <button
            onClick={handleDelete}
            title="Remove source"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 26,
              height: 26,
              background: 'transparent',
              color: 'var(--fg-muted)',
              border: '1px solid transparent',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
            }}
          >
            <IconTrash size={13} />
          </button>
        </div>
      </div>

      {/* Crawl history rows */}
      {showHistory && (
        <div className="flex flex-col" style={{ gap: 4, marginTop: 10 }}>
          {crawlJobs.length === 0 ? (
            <p style={{ fontSize: 11, color: 'var(--fg-faint)', margin: 0 }}>No crawl jobs yet</p>
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
                  {job.started_at ? timeAgo(job.started_at) : '—'}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)' }}>
                  {job.documents_indexed}/{job.documents_found} docs
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-faint)' }}>
                  {job.duration_seconds != null ? `${job.duration_seconds.toFixed(1)}s` : '—'}
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

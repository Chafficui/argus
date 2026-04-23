import { useState } from 'react'
import api from '../api/client'

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

const typeBadgeColors: Record<string, string> = {
  website: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  rss: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  serp: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
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
  const [confirmDelete, setConfirmDelete] = useState(false)

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
    if (!confirmDelete) {
      setConfirmDelete(true)
      setTimeout(() => setConfirmDelete(false), 3000)
      return
    }
    try {
      await api.delete(`/api/sources/${source.id}`)
      onDelete(source.id)
    } catch (err) {
      console.error('Failed to delete source', err)
    }
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-white truncate">{source.name}</h3>
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded-full border ${
                typeBadgeColors[source.source_type] || 'bg-slate-700 text-slate-300'
              }`}
            >
              {source.source_type}
            </span>
          </div>
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-500 hover:text-blue-400 transition-colors truncate block"
          >
            {source.url.length > 60 ? source.url.slice(0, 60) + '...' : source.url}
          </a>
          {source.search_query && (
            <p className="text-xs text-purple-400 mt-1">Query: {source.search_query}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleDelete}
            className={`px-2.5 py-1 text-xs rounded-lg transition-colors ${
              confirmDelete
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'text-slate-500 hover:text-red-400 hover:bg-slate-800'
            }`}
          >
            {confirmDelete ? 'Confirm?' : 'Delete'}
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-800">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span>
            Last crawled:{' '}
            {source.last_crawled_at ? timeAgo(source.last_crawled_at) : 'never'}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${source.is_active ? 'bg-emerald-400' : 'bg-slate-600'}`}
          />
        </div>
        <button
          onClick={loadCrawlHistory}
          disabled={loadingHistory}
          className="text-xs text-slate-400 hover:text-blue-400 transition-colors"
        >
          {loadingHistory ? 'Loading...' : showHistory ? 'Hide history' : 'Crawl history'}
        </button>
      </div>

      {/* Crawl history */}
      {showHistory && (
        <div className="mt-3 space-y-2">
          {crawlJobs.length === 0 ? (
            <p className="text-xs text-slate-600">No crawl jobs yet</p>
          ) : (
            crawlJobs.map((job) => (
              <div
                key={job.id}
                className="flex items-center gap-3 px-3 py-2 bg-slate-800/50 rounded-lg text-xs"
              >
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    job.status === 'success' ? 'bg-emerald-400' : 'bg-red-400'
                  }`}
                />
                <span className="text-slate-400">{timeAgo(job.started_at)}</span>
                <span className="text-slate-500">
                  {job.documents_indexed}/{job.documents_found} docs
                </span>
                <span className="text-slate-600">{job.duration_seconds.toFixed(1)}s</span>
                {job.error_message && (
                  <span className="text-red-400 truncate">{job.error_message}</span>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

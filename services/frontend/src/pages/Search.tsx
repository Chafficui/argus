import { useState, useRef, useEffect } from 'react'
import api from '../api/client'
import { Eyebrow } from '../components/Brand'
import { IconSearch, IconSparkle, IconClock, IconClose } from '../components/Icons'
import SourceFilter from '../components/SourceFilter'
import SearchResultCard from '../components/SearchResultCard'

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

interface SearchResponse {
  query: string
  results: SearchResult[]
  total: number
}

const HISTORY_KEY = 'argus-search-history'
const MAX_HISTORY = 20

function loadSearchHistory(): string[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveSearchHistory(history: string[]) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)))
}

export default function Search() {
  const [query, setQuery] = useState('')
  const [focus, setFocus] = useState(false)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [error, setError] = useState('')
  const [sourceIds, setSourceIds] = useState<string[]>([])
  const [searched, setSearched] = useState(false)
  const [history, setHistory] = useState<string[]>(loadSearchHistory)
  const [showHistory, setShowHistory] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowHistory(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const addToHistory = (q: string) => {
    const trimmed = q.trim()
    if (!trimmed) return
    const filtered = history.filter((h) => h !== trimmed)
    const updated = [trimmed, ...filtered].slice(0, MAX_HISTORY)
    setHistory(updated)
    saveSearchHistory(updated)
  }

  const removeFromHistory = (q: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const updated = history.filter((h) => h !== q)
    setHistory(updated)
    saveSearchHistory(updated)
  }

  const clearHistory = () => {
    setHistory([])
    saveSearchHistory([])
  }

  const search = async (searchQuery?: string) => {
    const q = searchQuery || query
    if (!q.trim()) return
    setLoading(true)
    setError('')
    setResponse(null)
    setSearched(true)
    setShowHistory(false)
    if (searchQuery) setQuery(searchQuery)

    addToHistory(q.trim())

    try {
      const res = await api.post('/api/search/', {
        query: q.trim(),
        top_k: 20,
        min_score: 0.4,
        ...(sourceIds.length > 0 ? { source_ids: sourceIds } : {}),
      })
      setResponse(res.data)
    } catch (err) {
      console.error('Search failed', err)
      setError('Search failed — check that the backend is running and Milvus has indexed documents.')
    } finally {
      setLoading(false)
    }
  }

  const hasResults = response && response.results.length > 0

  // Filter history based on current query
  const filteredHistory = query.trim()
    ? history.filter((h) => h.toLowerCase().includes(query.toLowerCase()) && h !== query)
    : history

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '36px 36px 80px' }}>
      {/* Hero state when no search yet */}
      {!searched && (
        <div className="text-center" style={{ padding: '60px 0 40px' }}>
          <img
            src="/argus-logo.png"
            width="64"
            height="64"
            style={{ filter: 'drop-shadow(0 0 24px rgba(34,211,238,0.35))', margin: '0 auto' }}
            alt=""
          />
          <h1
            style={{
              margin: '18px 0 6px',
              fontFamily: 'var(--font-display)',
              fontSize: 36,
              fontWeight: 600,
              color: 'var(--fg-bright)',
              letterSpacing: '0.02em',
            }}
          >
            Search
          </h1>
          <p style={{ color: 'var(--fg-muted)', fontSize: 14, margin: 0 }}>
            Semantic search across everything Argus has indexed. Results are ranked by relevance.
          </p>
        </div>
      )}

      {/* Search bar + source filter */}
      <div className="flex items-center" style={{ gap: 10, marginBottom: searched ? 28 : 0 }}>
        <div
          ref={dropdownRef}
          className="flex-1"
          style={{ position: 'relative' }}
        >
          <div
            style={{
              background: 'var(--bg-surface-2)',
              border: `1px solid ${focus ? 'var(--line-active)' : 'var(--line-strong)'}`,
              borderRadius: 'var(--radius-xl)',
              padding: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: focus ? 'var(--glow-signal)' : 'none',
              transition: 'all 150ms',
            }}
          >
            <IconSearch size={18} style={{ color: 'var(--core-400)', flexShrink: 0 }} />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => {
                setFocus(true)
                if (history.length > 0) setShowHistory(true)
              }}
              onBlur={() => setFocus(false)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  search()
                  setShowHistory(false)
                }
              }}
              placeholder="Search across your indexed sources..."
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                fontFamily: 'var(--font-sans)',
                fontSize: 16,
                color: 'var(--fg-bright)',
              }}
            />
            <button
              onClick={() => search()}
              disabled={loading || !query.trim()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                background: 'linear-gradient(180deg, #2FBBD5, #0E7490)',
                color: '#031218',
                border: '1px solid rgba(34,211,238,0.6)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 14px',
                fontSize: 12,
                fontWeight: 600,
                letterSpacing: '0.04em',
                cursor: loading ? 'wait' : 'pointer',
                opacity: loading || !query.trim() ? 0.5 : 1,
                flexShrink: 0,
              }}
            >
              <IconSparkle size={12} /> Search
            </button>
          </div>

          {/* Search history dropdown */}
          {showHistory && filteredHistory.length > 0 && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: 4,
                background: 'var(--bg-surface-2)',
                border: '1px solid var(--line-strong)',
                borderRadius: 'var(--radius-lg)',
                padding: '6px 0',
                zIndex: 50,
                maxHeight: 300,
                overflowY: 'auto',
              }}
            >
              <div
                className="flex items-center justify-between"
                style={{ padding: '6px 14px 8px', borderBottom: '1px solid var(--line-hairline)' }}
              >
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--fg-subtle)' }}>
                  Recent searches
                </span>
                <button
                  onMouseDown={(e) => { e.preventDefault(); clearHistory() }}
                  style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-faint)', background: 'transparent', border: 'none', cursor: 'pointer' }}
                >
                  Clear all
                </button>
              </div>
              {filteredHistory.map((h) => (
                <div
                  key={h}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    search(h)
                  }}
                  className="flex items-center justify-between"
                  style={{
                    padding: '8px 14px',
                    cursor: 'pointer',
                    transition: 'background 100ms',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-hover)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <div className="flex items-center" style={{ gap: 10, minWidth: 0, flex: 1 }}>
                    <IconClock size={12} style={{ color: 'var(--fg-faint)', flexShrink: 0 }} />
                    <span className="truncate" style={{ fontSize: 13, color: 'var(--fg-body)' }}>
                      {h}
                    </span>
                  </div>
                  <button
                    onMouseDown={(e) => removeFromHistory(h, e)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--fg-faint)',
                      cursor: 'pointer',
                      padding: 2,
                      flexShrink: 0,
                    }}
                  >
                    <IconClose size={10} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <SourceFilter selectedIds={sourceIds} onChange={setSourceIds} />
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center" style={{ padding: '60px 0' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--fg-subtle)' }}>
            Searching...
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div
          style={{
            marginTop: 24,
            padding: '14px 18px',
            background: 'var(--status-alert-a10)',
            border: '1px solid rgba(248,113,113,0.25)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--status-alert)',
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      {/* Results */}
      {!loading && hasResults && (
        <div>
          <Eyebrow count={response.total} color="var(--signal-400)">
            Results
          </Eyebrow>

          <div className="flex flex-col" style={{ gap: 10, marginTop: 14 }}>
            {response.results.map((r) => (
              <SearchResultCard key={r.chunk_id} result={r} />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && searched && response && response.results.length === 0 && (
        <div className="text-center" style={{ padding: '60px 0' }}>
          <p style={{ color: 'var(--fg-subtle)', fontSize: 14 }}>
            No results found — try a different query or add more sources.
          </p>
        </div>
      )}
    </div>
  )
}

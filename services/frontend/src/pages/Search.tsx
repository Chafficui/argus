import { useState } from 'react'
import api from '../api/client'
import { Eyebrow } from '../components/Brand'
import { IconSearch, IconSparkle } from '../components/Icons'
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

export default function Search() {
  const [query, setQuery] = useState('')
  const [focus, setFocus] = useState(false)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [error, setError] = useState('')
  const [sourceIds, setSourceIds] = useState<string[]>([])
  const [searched, setSearched] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setResponse(null)
    setSearched(true)

    try {
      const res = await api.post('/api/search/', {
        query: query.trim(),
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
          className="flex-1"
          style={{
            position: 'relative',
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
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setFocus(true)}
            onBlur={() => setFocus(false)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') search()
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
            onClick={search}
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
              boxShadow: 'var(--glow-core)',
              opacity: loading || !query.trim() ? 0.5 : 1,
              flexShrink: 0,
            }}
          >
            <IconSparkle size={12} /> Search
          </button>
        </div>

        <SourceFilter selectedIds={sourceIds} onChange={setSourceIds} />
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center" style={{ padding: '60px 0' }}>
          <span
            className="pulse-core"
            style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--core-500)' }}
          />
          <span
            style={{
              marginLeft: 12,
              fontFamily: 'var(--font-display)',
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--core-400)',
            }}
          >
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

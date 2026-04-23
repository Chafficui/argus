import { useEffect, useState } from 'react'
import api from '../api/client'
import SourceCard from '../components/SourceCard'
import AddSourceModal from '../components/AddSourceModal'
import { Eyebrow } from '../components/Brand'
import Button from '../components/Button'
import { IconPlus } from '../components/Icons'

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

function Stat({
  label,
  value,
  hint,
  live,
  mono,
}: {
  label: string
  value: string | number
  hint: string
  live?: boolean
  mono?: boolean
}) {
  return (
    <div style={{ background: 'var(--bg-surface-2)', padding: '18px 20px' }}>
      <div className="flex items-center" style={{ gap: 6 }}>
        {live && (
          <span
            className="pulse-core"
            style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--core-500)' }}
          />
        )}
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: live ? 'var(--core-400)' : 'var(--fg-muted)',
          }}
        >
          {label}
        </span>
      </div>
      <div
        style={{
          fontFamily: mono ? 'var(--font-mono)' : 'var(--font-display)',
          fontSize: 28,
          fontWeight: 600,
          color: 'var(--fg-bright)',
          letterSpacing: '0.02em',
          marginTop: 6,
        }}
      >
        {value}
      </div>
      <div style={{ fontSize: 11, color: 'var(--fg-subtle)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
        {hint}
      </div>
    </div>
  )
}

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  const fetchSources = async () => {
    try {
      const res = await api.get('/api/sources/')
      setSources(res.data)
    } catch (err) {
      console.error('Failed to fetch sources', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    api.get('/api/sources/').then((res) => {
      setSources(res.data)
      setLoading(false)
    }).catch((err) => {
      console.error('Failed to fetch sources', err)
      setLoading(false)
    })
  }, [])

  const handleDelete = (id: string) => {
    setSources((prev) => prev.filter((s) => s.id !== id))
  }

  const liveSources = sources.filter((s) => s.is_active).length

  return (
    <div style={{ padding: '28px 36px 40px', maxWidth: 1100, margin: '0 auto' }}>
      {/* Page header */}
      <div className="flex items-end justify-between" style={{ marginBottom: 28 }}>
        <div>
          <Eyebrow count={sources.length}>Sources</Eyebrow>
          <h1
            style={{
              margin: '8px 0 0',
              fontFamily: 'var(--font-display)',
              fontSize: 32,
              fontWeight: 600,
              color: 'var(--fg-bright)',
              letterSpacing: '0.02em',
            }}
          >
            What Argus watches
          </h1>
          <p style={{ margin: '6px 0 0', color: 'var(--fg-muted)', fontSize: 14 }}>
            Websites, feeds, and queries Argus crawls and indexes into your corpus.
          </p>
        </div>
        <Button variant="primary" icon={<IconPlus size={14} />} onClick={() => setShowModal(true)}>
          Add source
        </Button>
      </div>

      {/* Stats rail */}
      {!loading && sources.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 1,
            background: 'var(--line-default)',
            border: '1px solid var(--line-default)',
            borderRadius: 'var(--radius-xl)',
            overflow: 'hidden',
            marginBottom: 24,
          }}
        >
          <Stat label="Sources" value={sources.length} hint="monitored" />
          <Stat label="Active" value={liveSources} hint="crawling now" live />
          <Stat label="Docs" value="—" hint="indexed · total" />
          <Stat label="Tokens" value="—" hint="estimated" mono />
        </div>
      )}

      {/* Source list */}
      {loading ? (
        <div className="flex items-center justify-center" style={{ padding: '80px 0' }}>
          <div
            className="pulse-core"
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--core-500)',
            }}
          />
        </div>
      ) : sources.length === 0 ? (
        <div className="text-center" style={{ padding: '80px 0' }}>
          <p style={{ color: 'var(--fg-subtle)', marginBottom: 16, fontSize: 14 }}>
            No sources yet. Add one to start watching.
          </p>
          <Button variant="primary" icon={<IconPlus size={14} />} onClick={() => setShowModal(true)}>
            Add your first source
          </Button>
        </div>
      ) : (
        <div className="flex flex-col" style={{ gap: 10 }}>
          {sources.map((source) => (
            <SourceCard key={source.id} source={source} onDelete={handleDelete} />
          ))}
        </div>
      )}

      <AddSourceModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onCreated={fetchSources}
      />
    </div>
  )
}

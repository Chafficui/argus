import { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import SourceCard from '../components/SourceCard'
import AddSourceModal from '../components/AddSourceModal'

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

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  const fetchSources = useCallback(async () => {
    try {
      const res = await api.get('/api/sources/')
      setSources(res.data)
    } catch (err) {
      console.error('Failed to fetch sources', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSources()
  }, [fetchSources])

  const handleDelete = (id: string) => {
    setSources((prev) => prev.filter((s) => s.id !== id))
  }

  return (
    <div className="p-8 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Sources</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage the websites, RSS feeds, and search queries Argus monitors.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Add Source
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : sources.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-slate-500 mb-4">No sources yet. Add one to get started.</p>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
          >
            Add your first source
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
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

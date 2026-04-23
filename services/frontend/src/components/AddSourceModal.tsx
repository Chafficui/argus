import { useState } from 'react'
import api from '../api/client'
import Button from './Button'
import { TypeMeta } from './SourceTypeBadge'
import { IconClose, IconGlobe, IconRss, IconSearch } from './Icons'

interface AddSourceModalProps {
  open: boolean
  onClose: () => void
  onCreated: () => void
}

const typeOptions = [
  { value: 'website', label: 'Website', desc: 'Crawl pages from a domain', Icon: IconGlobe },
  { value: 'rss', label: 'RSS feed', desc: 'Ingest items as they publish', Icon: IconRss },
  { value: 'serp', label: 'SERP query', desc: 'Watch search results over time', Icon: IconSearch },
]

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label
      style={{
        display: 'block',
        fontFamily: 'var(--font-display)',
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: 'var(--fg-muted)',
        marginBottom: 6,
      }}
    >
      {children}
    </label>
  )
}

function Input({
  value,
  onChange,
  placeholder,
  type = 'text',
  required,
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  type?: string
  required?: boolean
}) {
  const [focus, setFocus] = useState(false)
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => setFocus(true)}
      onBlur={() => setFocus(false)}
      placeholder={placeholder}
      required={required}
      style={{
        width: '100%',
        boxSizing: 'border-box',
        padding: '10px 12px',
        background: 'var(--bg-surface-3)',
        border: `1px solid ${focus ? 'var(--line-active)' : 'var(--line-default)'}`,
        borderRadius: 'var(--radius-lg)',
        color: 'var(--fg-bright)',
        fontFamily: 'var(--font-sans)',
        fontSize: 13,
        outline: 'none',
        transition: 'border-color 150ms',
      }}
    />
  )
}

export default function AddSourceModal({ open, onClose, onCreated }: AddSourceModalProps) {
  const [sourceType, setSourceType] = useState('website')
  const [url, setUrl] = useState('')
  const [name, setName] = useState('')
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!open) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await api.post('/api/sources/', {
        name: name || url || query,
        url: sourceType === 'serp' ? `https://search.argus.local/?q=${encodeURIComponent(query)}` : url,
        source_type: sourceType,
        ...(sourceType === 'serp' ? { search_query: query } : {}),
      })
      setName('')
      setUrl('')
      setSourceType('website')
      setQuery('')
      onCreated()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setError(axiosErr.response?.data?.detail || 'Failed to create source')
      } else {
        setError('Failed to create source')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        background: 'rgba(2,4,15,0.78)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          position: 'relative',
          width: 460,
          background: 'var(--bg-surface-2)',
          border: '1px solid rgba(59,130,246,0.3)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-modal)',
          overflow: 'hidden',
        }}
      >
        {/* Top glow line */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 0,
            height: 1,
            background: 'linear-gradient(90deg, transparent, var(--signal-500), transparent)',
          }}
        />

        {/* Header */}
        <div className="flex items-center justify-between" style={{ padding: '18px 20px 0' }}>
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              color: 'var(--signal-400)',
            }}
          >
            New source
          </span>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--fg-subtle)',
              cursor: 'pointer',
              padding: 4,
            }}
          >
            <IconClose size={16} />
          </button>
        </div>

        <h2
          style={{
            margin: 0,
            padding: '8px 20px 4px',
            fontFamily: 'var(--font-display)',
            fontSize: 22,
            fontWeight: 600,
            color: 'var(--fg-bright)',
            letterSpacing: '0.02em',
          }}
        >
          Add source
        </h2>
        <p style={{ margin: 0, padding: '0 20px 16px', fontSize: 13, color: 'var(--fg-muted)' }}>
          Argus will crawl this source and index documents as they appear.
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ padding: '14px 20px 16px', borderTop: '1px solid var(--line-default)' }}>
            <Label>Type</Label>
            <div className="grid grid-cols-3" style={{ gap: 8, marginBottom: 14 }}>
              {typeOptions.map((t) => {
                const selected = sourceType === t.value
                const meta = TypeMeta[t.value]
                return (
                  <div
                    key={t.value}
                    onClick={() => setSourceType(t.value)}
                    style={{
                      padding: 12,
                      borderRadius: 'var(--radius-md)',
                      background: selected ? meta.bg : 'var(--bg-surface-3)',
                      border: `1px solid ${selected ? meta.border : 'var(--line-default)'}`,
                      cursor: 'pointer',
                      transition: 'all 150ms',
                    }}
                  >
                    <t.Icon size={16} style={{ color: selected ? meta.color : 'var(--fg-muted)' }} />
                    <div
                      style={{
                        marginTop: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        color: selected ? 'var(--fg-bright)' : 'var(--fg-body)',
                      }}
                    >
                      {t.label}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--fg-subtle)', marginTop: 2, lineHeight: 1.4 }}>
                      {t.desc}
                    </div>
                  </div>
                )
              })}
            </div>

            {sourceType === 'serp' ? (
              <div style={{ marginBottom: 12 }}>
                <Label>Query</Label>
                <Input
                  value={query}
                  onChange={setQuery}
                  placeholder="EU AI Act 2026 compliance"
                  required
                />
              </div>
            ) : (
              <div style={{ marginBottom: 12 }}>
                <Label>URL</Label>
                <Input
                  value={url}
                  onChange={setUrl}
                  placeholder={sourceType === 'rss' ? 'https://example.com/feed.xml' : 'https://example.com'}
                  type="url"
                  required
                />
              </div>
            )}

            <Label>Name · optional</Label>
            <Input value={name} onChange={setName} placeholder="Human-readable label" />
          </div>

          {error && (
            <p
              style={{
                margin: '0 20px 12px',
                fontSize: 12,
                color: 'var(--status-alert)',
                background: 'var(--status-alert-a10)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
              }}
            >
              {error}
            </p>
          )}

          <div
            className="flex justify-end"
            style={{ gap: 8, padding: '12px 20px 16px', borderTop: '1px solid var(--line-default)' }}
          >
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? 'Adding...' : 'Add source'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

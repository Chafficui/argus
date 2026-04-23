import { useState, useEffect, useRef } from 'react'
import api from '../api/client'
import { IconSources } from './Icons'

interface Source {
  id: string
  name: string
  source_type: string
}

interface SourceFilterProps {
  selectedIds: string[]
  onChange: (ids: string[]) => void
}

export default function SourceFilter({ selectedIds, onChange }: SourceFilterProps) {
  const [sources, setSources] = useState<Source[]>([])
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.get('/api/sources/').then((res) => {
      setSources(res.data.map((s: Source) => ({ id: s.id, name: s.name, source_type: s.source_type })))
    }).catch(() => {})
  }, [])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const toggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((s) => s !== id))
    } else {
      onChange([...selectedIds, id])
    }
  }

  const label =
    selectedIds.length === 0
      ? 'All sources'
      : selectedIds.length === 1
        ? sources.find((s) => s.id === selectedIds[0])?.name || '1 source'
        : `${selectedIds.length} sources`

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center"
        style={{
          gap: 8,
          padding: '7px 12px',
          background: 'var(--bg-surface-2)',
          border: `1px solid ${open ? 'var(--line-active)' : 'var(--line-default)'}`,
          borderRadius: 'var(--radius-lg)',
          color: selectedIds.length > 0 ? 'var(--signal-300)' : 'var(--fg-muted)',
          fontFamily: 'var(--font-sans)',
          fontSize: 12,
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 150ms',
          whiteSpace: 'nowrap',
        }}
      >
        <IconSources size={14} />
        {label}
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M2.5 4L5 6.5L7.5 4" />
        </svg>
      </button>

      {open && sources.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: 4,
            minWidth: 220,
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--line-strong)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-modal)',
            zIndex: 50,
            overflow: 'hidden',
          }}
        >
          {/* All sources option */}
          <div
            onClick={() => { onChange([]); setOpen(false) }}
            className="flex items-center"
            style={{
              gap: 8,
              padding: '10px 14px',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: selectedIds.length === 0 ? 600 : 400,
              color: selectedIds.length === 0 ? 'var(--signal-300)' : 'var(--fg-body)',
              borderBottom: '1px solid var(--line-hairline)',
              transition: 'background 100ms',
              background: 'transparent',
            }}
          >
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: 'var(--radius-xs)',
                border: `1px solid ${selectedIds.length === 0 ? 'var(--signal-500)' : 'var(--line-default)'}`,
                background: selectedIds.length === 0 ? 'var(--signal-500-a20)' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {selectedIds.length === 0 && (
                <svg width="8" height="8" viewBox="0 0 8 8" fill="none" stroke="var(--signal-300)" strokeWidth="1.5">
                  <path d="M1.5 4L3.5 6L6.5 2" />
                </svg>
              )}
            </span>
            All sources
          </div>

          {sources.map((s) => {
            const selected = selectedIds.includes(s.id)
            return (
              <div
                key={s.id}
                onClick={() => toggle(s.id)}
                className="flex items-center"
                style={{
                  gap: 8,
                  padding: '9px 14px',
                  cursor: 'pointer',
                  fontSize: 12,
                  color: selected ? 'var(--fg-bright)' : 'var(--fg-body)',
                  transition: 'background 100ms',
                  background: 'transparent',
                }}
              >
                <span
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: 'var(--radius-xs)',
                    border: `1px solid ${selected ? 'var(--signal-500)' : 'var(--line-default)'}`,
                    background: selected ? 'var(--signal-500-a20)' : 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  {selected && (
                    <svg width="8" height="8" viewBox="0 0 8 8" fill="none" stroke="var(--signal-300)" strokeWidth="1.5">
                      <path d="M1.5 4L3.5 6L6.5 2" />
                    </svg>
                  )}
                </span>
                <span className="truncate">{s.name}</span>
                <span
                  style={{
                    marginLeft: 'auto',
                    fontFamily: 'var(--font-display)',
                    fontSize: 9,
                    fontWeight: 600,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: 'var(--fg-subtle)',
                  }}
                >
                  {s.source_type}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

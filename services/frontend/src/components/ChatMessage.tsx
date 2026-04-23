import { useState } from 'react'
import Markdown from 'react-markdown'
import { IconCopy, IconCheck, IconExternal } from './Icons'
import { Eyebrow } from './Brand'

interface SourceChunk {
  chunk_id: string
  title: string
  url: string
  score: number
  source_name: string | null
  text: string
}

interface ChatMessageProps {
  role: 'user' | 'assistant'
  text: string
  sources?: SourceChunk[]
  streaming?: boolean
}

function MiniBtn({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '4px 8px',
        background: 'transparent',
        color: 'var(--fg-subtle)',
        border: '1px solid var(--line-default)',
        borderRadius: 'var(--radius-sm)',
        fontFamily: 'var(--font-sans)',
        fontSize: 11,
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all 150ms',
      }}
    >
      {children}
    </button>
  )
}

export default function ChatMessage({ role, text, sources, streaming }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const [showSources, setShowSources] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div
          style={{
            maxWidth: '80%',
            background: 'rgba(59, 130, 246, 0.12)',
            border: '1px solid rgba(59, 130, 246, 0.28)',
            borderRadius: '12px 12px 2px 12px',
            padding: '12px 16px',
            fontSize: 14,
            color: 'var(--fg-bright)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {text}
        </div>
      </div>
    )
  }

  return (
    <div className="flex" style={{ gap: 12, alignItems: 'flex-start' }}>
      <div
        className="shrink-0 inline-flex items-center justify-center"
        style={{
          width: 28,
          height: 28,
          background: 'var(--bg-surface-3)',
          border: '1px solid var(--line-strong)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <img src="/argus-logo.png" width="18" height="18" alt="" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="chat-prose" style={{ fontSize: 14.5, lineHeight: 1.7, color: 'var(--fg-body)' }}>
          <Markdown>{text}</Markdown>
          {streaming && (
            <span
              className="pulse-core"
              style={{
                display: 'inline-block',
                width: 8,
                height: 14,
                marginLeft: 2,
                marginBottom: -2,
                background: 'var(--core-500)',
                borderRadius: 1,
              }}
            />
          )}
        </div>

        {!streaming && (
          <div className="flex items-center" style={{ gap: 6, marginTop: 10 }}>
            <MiniBtn onClick={handleCopy}>
              {copied ? (
                <>
                  <IconCheck size={11} /> Copied
                </>
              ) : (
                <>
                  <IconCopy size={11} /> Copy
                </>
              )}
            </MiniBtn>

            {sources && sources.length > 0 && (
              <MiniBtn onClick={() => setShowSources(!showSources)}>
                {showSources ? 'Hide sources' : `Sources (${sources.length})`}
              </MiniBtn>
            )}
          </div>
        )}

        {/* Collapsible source citations */}
        {showSources && sources && sources.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Eyebrow color="var(--signal-400)">Sources used</Eyebrow>
            <div className="flex flex-col" style={{ gap: 6, marginTop: 8 }}>
              {sources.map((s, i) => (
                <div
                  key={s.chunk_id || i}
                  style={{
                    background: 'var(--bg-surface-2)',
                    border: '1px solid var(--line-default)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '10px 14px',
                  }}
                >
                  <div className="flex items-start justify-between" style={{ gap: 8 }}>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--fg-bright)', lineHeight: 1.3 }}>
                        {s.title || 'Untitled'}
                      </div>
                      <div className="flex items-center" style={{ gap: 6, marginTop: 4 }}>
                        {s.source_name && (
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-muted)' }}>
                            {s.source_name}
                          </span>
                        )}
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: 10,
                            color: 'var(--signal-400)',
                            padding: '1px 6px',
                            background: 'var(--signal-500-a10)',
                            borderRadius: 'var(--radius-pill)',
                          }}
                        >
                          {Math.round(s.score * 100)}%
                        </span>
                      </div>
                    </div>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: 'var(--fg-subtle)', flexShrink: 0 }}
                    >
                      <IconExternal size={12} />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

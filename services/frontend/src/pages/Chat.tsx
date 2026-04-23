import { useState, useRef, useEffect, useCallback } from 'react'
import api from '../api/client'
import { Eyebrow } from '../components/Brand'
import { IconArrow, IconTrash } from '../components/Icons'
import SourceFilter from '../components/SourceFilter'
import ChatMessage from '../components/ChatMessage'

interface SourceChunk {
  chunk_id: string
  document_id: string
  source_id: string
  title: string
  url: string
  text: string
  score: number
  source_name: string | null
  chunk_index: number
}

interface Message {
  role: 'user' | 'assistant'
  text: string
  sources?: SourceChunk[]
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sourceIds, setSourceIds] = useState<string[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading, scrollToBottom])

  const resizeTextarea = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg: Message = { role: 'user', text: input.trim() }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      const res = await api.post('/api/search/ask', {
        query: userMsg.text,
        top_k: 8,
        min_score: 0.4,
        ...(sourceIds.length > 0 ? { source_ids: sourceIds } : {}),
      })
      const assistantMsg: Message = {
        role: 'assistant',
        text: res.data.answer,
        sources: res.data.sources,
      }
      setMessages((m) => [...m, assistantMsg])
    } catch (err) {
      console.error('Chat failed', err)
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: 'Something went wrong. Make sure the backend and Ollama are running.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const clearConversation = () => {
    setMessages([])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col" style={{ height: '100vh' }}>
      {/* Header */}
      <header
        className="flex items-center justify-between shrink-0"
        style={{
          padding: '14px 28px',
          borderBottom: '1px solid var(--line-default)',
          background: 'var(--bg-surface-1)',
        }}
      >
        <div className="flex items-center" style={{ gap: 16 }}>
          <div>
            <Eyebrow>Chat</Eyebrow>
            <div
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--fg-bright)',
                letterSpacing: '0.02em',
                marginTop: 2,
              }}
            >
              Research assistant
            </div>
          </div>
          <SourceFilter selectedIds={sourceIds} onChange={setSourceIds} />
        </div>

        <div className="flex items-center" style={{ gap: 12 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)' }}>
            {messages.length} messages
          </span>
          {messages.length > 0 && (
            <button
              onClick={clearConversation}
              className="flex items-center"
              style={{
                gap: 5,
                padding: '5px 10px',
                background: 'transparent',
                border: '1px solid var(--line-default)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--fg-subtle)',
                fontFamily: 'var(--font-sans)',
                fontSize: 11,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 150ms',
              }}
            >
              <IconTrash size={11} /> Clear
            </button>
          )}
        </div>
      </header>

      {/* Message thread */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto" style={{ padding: '28px 40px' }}>
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center" style={{ padding: '80px 0' }}>
            <img
              src="/argus-logo.png"
              width="48"
              height="48"
              style={{ filter: 'drop-shadow(0 0 16px rgba(34,211,238,0.3))', marginBottom: 16 }}
              alt=""
            />
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 22,
                fontWeight: 600,
                color: 'var(--fg-bright)',
                letterSpacing: '0.02em',
                marginBottom: 6,
              }}
            >
              Ask Argus
            </h2>
            <p style={{ color: 'var(--fg-muted)', fontSize: 14, maxWidth: 400, textAlign: 'center' }}>
              Ask questions across your indexed sources. Argus will retrieve relevant chunks and generate an answer with citations.
            </p>
          </div>
        ) : (
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            <div className="flex flex-col" style={{ gap: 24 }}>
              {messages.map((m, i) => (
                <ChatMessage
                  key={i}
                  role={m.role}
                  text={m.text}
                  sources={m.sources}
                />
              ))}

              {/* Typing indicator */}
              {loading && (
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
                  <div className="flex items-center" style={{ gap: 4, paddingTop: 8 }}>
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          background: 'var(--core-500)',
                          opacity: 0.6,
                          animation: `pulse-core 1.4s ease-in-out ${i * 0.2}s infinite`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Input area — fixed at bottom */}
      <div
        className="shrink-0"
        style={{
          padding: '16px 28px 22px',
          borderTop: '1px solid var(--line-default)',
          background: 'var(--bg-surface-1)',
        }}
      >
        <div
          className="flex items-end"
          style={{
            maxWidth: 760,
            margin: '0 auto',
            gap: 12,
            padding: 12,
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--line-strong)',
            borderRadius: 'var(--radius-xl)',
          }}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              resizeTextarea()
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            rows={1}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              fontFamily: 'var(--font-sans)',
              fontSize: 14,
              color: 'var(--fg-bright)',
              resize: 'none',
              lineHeight: 1.5,
              maxHeight: 120,
            }}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              background: 'linear-gradient(180deg, #2FBBD5, #0E7490)',
              color: '#031218',
              border: '1px solid rgba(34,211,238,0.6)',
              borderRadius: 'var(--radius-md)',
              padding: '6px 12px',
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: '0.04em',
              cursor: loading ? 'wait' : 'pointer',
              boxShadow: 'var(--glow-core)',
              opacity: loading || !input.trim() ? 0.5 : 1,
              flexShrink: 0,
            }}
          >
            <IconArrow size={12} /> Send
          </button>
        </div>
        <div
          style={{
            maxWidth: 760,
            margin: '6px auto 0',
            textAlign: 'center',
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--fg-faint)',
          }}
        >
          Enter to send · Shift+Enter for newline
        </div>
      </div>
    </div>
  )
}

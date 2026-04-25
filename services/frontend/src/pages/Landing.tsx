import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { Brand } from '../components/Brand'
import { IconSearch } from '../components/Icons'

const CAPS = [
  { n: '01', title: 'Continuous crawl', desc: 'Playwright-backed fetchers run on a schedule per source. New documents are chunked, embedded, and indexed within seconds of publication.' },
  { n: '02', title: 'Three ingestion modes', desc: 'Crawl a whole domain, subscribe to an RSS feed, or watch a search query over time. All three land in the same corpus.' },
  { n: '03', title: 'Hybrid retrieval', desc: 'Milvus vector search plus BM25 keyword match, then cross-encoder rerank. Tuned for recall on small, specific corpora.' },
  { n: '04', title: 'Grounded answers', desc: 'Every claim carries a citation to the source chunk. No citation, no claim — the model is instructed to abstain.' },
  { n: '05', title: 'Retrieval trace', desc: 'See exactly which chunks were retrieved, which were reranked up, and which made it into the final context window.' },
  { n: '06', title: 'On-prem by default', desc: 'One docker compose stack. Your queries, your documents, your inference. No third-party API calls unless you wire them.' },
]

const STAGES = [
  { n: '01', stage: 'Ingest', desc: 'Playwright crawler, RSS parser, or SERP tracker. Polite rate-limits, robots-aware, retry-on-failure.', tag: 'per-source schedule' },
  { n: '02', stage: 'Index', desc: 'Deduplicate, chunk, embed. Milvus vector index + Postgres full-text for BM25 fallback.', tag: '~4s / doc' },
  { n: '03', stage: 'Retrieve', desc: 'Hybrid query: vector top-k + BM25 top-k, union, then cross-encoder rerank down to context budget.', tag: 'k=12 · k_rerank=6' },
  { n: '04', stage: 'Answer', desc: 'Prompted to cite every claim, abstain if unsupported. Streams tokens; citations resolve live.', tag: 'local LLMs' },
]

const EyeIcon = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" />
    <circle cx={12} cy={12} r={3} />
  </svg>
)

export default function Landing() {
  const { authenticated, login } = useAuth()
  const navigate = useNavigate()

  const handleCta = () => (authenticated ? navigate('/sources') : login())

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-void)', color: 'var(--fg-body)', overflowX: 'hidden' }}>
      {/* ── Nav ── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        backdropFilter: 'blur(8px)',
        background: 'rgba(2,4,15,0.7)',
        borderBottom: '1px solid var(--line-hairline)',
      }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '18px 48px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Brand size={28} compact />
          <div style={{ display: 'flex', gap: 28, alignItems: 'center' }}>
            {['Capabilities', 'How it works', 'Deploy'].map((label) => (
              <a
                key={label}
                href={`#${label.toLowerCase().replace(/ /g, '-')}`}
                style={{
                  fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 600,
                  letterSpacing: '0.12em', textTransform: 'uppercase',
                  color: 'var(--fg-muted)', textDecoration: 'none', transition: 'color 150ms',
                }}
              >
                {label}
              </a>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={handleCta} style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '8px 16px', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--line-strong)', background: 'transparent',
              color: 'var(--fg-body)', fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 600,
              cursor: 'pointer', transition: 'all 150ms',
            }}>
              {authenticated ? 'Open dashboard' : 'Sign in'}
            </button>
            <a href="https://github.com/Chafficui/argus" target="_blank" rel="noopener noreferrer" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'linear-gradient(180deg, #2FBBD5, #0E7490)',
              color: '#031218',
              border: '1px solid rgba(34,211,238, 0.6)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 16px',
              fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 600,
              letterSpacing: '0.02em', cursor: 'pointer',
              boxShadow: 'var(--glow-core)',
              textDecoration: 'none', transition: 'all 150ms',
            }}>
              View on GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{
        position: 'relative',
        padding: '120px 0 140px',
        backgroundImage: 'var(--pattern-grid)',
        backgroundSize: 'var(--pattern-grid-size)',
        borderBottom: '1px solid var(--line-hairline)',
        overflow: 'hidden',
      }}>
        <div style={{ content: '""', position: 'absolute', left: 0, right: 0, top: 0, height: 1, background: 'linear-gradient(90deg, transparent, var(--signal-500), transparent)', opacity: 0.5 }} />
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', background: 'radial-gradient(ellipse at 50% 40%, transparent, var(--bg-void) 75%)' }} />
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 1280, margin: '0 auto', padding: '0 48px' }}>
          <img
            src="/argus-logo.png" alt=""
            style={{
              display: 'block',
              margin: '0 auto',
              width: 96, height: 96,
              borderRadius: 'var(--radius-xl)',
              filter: 'drop-shadow(0 0 40px rgba(34,211,238,0.4)) drop-shadow(0 0 12px rgba(34,211,238,0.6))',
              animation: 'hero-breathe 4s ease-in-out infinite',
            }}
          />
          <div style={{ marginTop: 28 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 600,
              letterSpacing: '0.2em', textTransform: 'uppercase',
              color: 'var(--signal-400)',
              padding: '4px 12px', borderRadius: 'var(--radius-pill)',
              background: 'var(--signal-500-a10)', border: '1px solid var(--signal-500-a20)',
            }}>
              <span className="pulse-core" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--core-500)' }} />
              On-prem research · open source
            </span>
          </div>
          <h1 style={{
            fontFamily: 'var(--font-display)', fontWeight: 600,
            fontSize: 'clamp(56px, 7vw, 88px)', lineHeight: 1.02,
            letterSpacing: '0.01em',
            color: 'var(--fg-bright)',
            margin: '28px 0 0',
          }}>
            See everything.<br />Remember everything.
          </h1>
          <p style={{
            fontSize: 19, lineHeight: 1.5,
            color: 'var(--fg-muted)',
            maxWidth: 620, margin: '24px auto 0',
          }}>
            Argus is the hundred-eyed research platform. One on-prem stack
            that crawls the sources you care about, indexes them forever, and
            answers questions across the corpus with cited evidence.
          </p>
          <div style={{ display: 'inline-flex', gap: 12, marginTop: 36 }}>
            <button onClick={handleCta} style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'linear-gradient(180deg, #2FBBD5, #0E7490)',
              color: '#031218',
              border: '1px solid rgba(34,211,238, 0.6)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 20px',
              fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 600,
              letterSpacing: '0.02em', cursor: 'pointer',
              boxShadow: 'var(--glow-core)',
              transition: 'all 150ms',
            }}>
              {authenticated ? 'Open dashboard' : 'Get started'} →
            </button>
            <a href="https://github.com/Chafficui/argus" target="_blank" rel="noopener noreferrer" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '12px 20px',
              color: 'var(--fg-body)', fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 600,
              border: '1px solid var(--line-strong)', borderRadius: 'var(--radius-md)',
              background: 'transparent', textDecoration: 'none',
              transition: 'all 150ms',
            }}>
              View source
            </a>
          </div>
        </div>
      </section>

      {/* ── Capabilities ── */}
      <section id="capabilities" style={{ padding: '120px 0' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 48px' }}>
          <div style={{ marginBottom: 56, maxWidth: 760 }}>
            <span style={{
              fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 600,
              letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--signal-400)',
            }}>Capabilities · 06</span>
            <h2 style={{
              fontFamily: 'var(--font-display)', fontSize: 44, fontWeight: 600,
              color: 'var(--fg-bright)', letterSpacing: '0.01em', lineHeight: 1.08,
              margin: '12px 0 0',
            }}>A console for watching the web.</h2>
            <p style={{ color: 'var(--fg-muted)', fontSize: 17, lineHeight: 1.55, margin: '18px 0 0' }}>
              Argus is built for analysts, compliance teams, and researchers
              who need to see the primary source — not a chatbot guessing.
              Every answer cites. Every source is one you chose.
            </p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
            {CAPS.map((c) => (
              <div key={c.n} style={{
                position: 'relative',
                padding: 24,
                background: 'var(--bg-surface-2)',
                border: '1px solid var(--line-default)',
                borderRadius: 'var(--radius-xl)',
                transition: 'all 200ms',
              }}>
                <span style={{
                  position: 'absolute', top: 24, right: 24,
                  fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-faint)', letterSpacing: '0.08em',
                }}>{c.n}</span>
                <div style={{
                  width: 40, height: 40, borderRadius: 'var(--radius-md)',
                  background: 'var(--signal-500-a10)', border: '1px solid var(--signal-500-a20)',
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--signal-300)', marginBottom: 16,
                }}>
                  <EyeIcon />
                </div>
                <h3 style={{
                  fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 600,
                  color: 'var(--fg-bright)', letterSpacing: '0.02em', margin: '0 0 8px',
                }}>{c.title}</h3>
                <p style={{ fontSize: 14, lineHeight: 1.55, color: 'var(--fg-muted)', margin: 0 }}>{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Showcase ── */}
      <section style={{
        background: 'var(--bg-surface-1)',
        borderTop: '1px solid var(--line-default)',
        borderBottom: '1px solid var(--line-default)',
        padding: '96px 0',
      }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 48px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 56, alignItems: 'center' }}>
            <div style={{
              position: 'relative',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--line-default)',
              borderRadius: 'var(--radius-xl)',
              padding: 24, overflow: 'hidden',
            }}>
              <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 1, background: 'linear-gradient(90deg, transparent, var(--signal-500), transparent)' }} />
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 14px',
                background: 'var(--bg-surface-3)',
                border: '1px solid var(--line-default)',
                borderRadius: 'var(--radius-lg)',
                marginBottom: 18,
              }}>
                <IconSearch size={16} style={{ color: 'var(--core-400)' }} />
                <span style={{ flex: 1, color: 'var(--fg-bright)', fontFamily: 'var(--font-sans)', fontSize: 13 }}>
                  Core obligations under the EU AI Act for foundation model providers?
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 18 }}>
                {[
                  { n: 1, url: 'artificialintelligenceact.eu' },
                  { n: 2, url: 'arxiv.org/abs/2403.06912' },
                  { n: 3, url: 'iapp.org' },
                ].map((src) => (
                  <div key={src.n} style={{
                    padding: '10px 12px',
                    background: 'var(--bg-surface-3)',
                    border: '1px solid var(--line-default)',
                    borderRadius: 'var(--radius-md)',
                    fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-muted)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    <span style={{ color: 'var(--signal-400)', marginRight: 4 }}>[{src.n}]</span>
                    {src.url}
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 13.5, lineHeight: 1.7, color: 'var(--fg-body)' }}>
                GPAI providers carry four core obligations under Articles 53–55
                <Cite n={1} />. They must maintain technical documentation covering training data and evaluation procedures
                <Cite n={1} /><Cite n={2} />, publish a detailed summary of training data
                <Cite n={3} />, and — for systemic-risk models — run adversarial testing and report serious incidents to the AI Office
                <Cite n={2} />.
              </div>
            </div>
            <div>
              <span style={{
                fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 600,
                letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--signal-400)',
              }}>Cited answers</span>
              <h3 style={{
                fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 600,
                color: 'var(--fg-bright)', letterSpacing: '0.01em', lineHeight: 1.15,
                margin: '12px 0 20px',
              }}>
                No claim without a citation.
              </h3>
              <p style={{ color: 'var(--fg-muted)', fontSize: 15, lineHeight: 1.65, margin: '0 0 14px' }}>
                Argus is instructed to abstain rather than hallucinate.
                Every span links back to the exact chunk of the
                exact source it came from — click the pill, read the quote,
                trust what you ship.
              </p>
              <p style={{ color: 'var(--fg-muted)', fontSize: 15, lineHeight: 1.65, margin: 0 }}>
                The retrieval trace shows what happened between
                the question and the answer: rewrite, retrieve, rerank,
                generate. Latency and chunk scores at every stage.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Pipeline ── */}
      <section id="how-it-works" style={{ padding: '120px 0' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 48px' }}>
          <div style={{ marginBottom: 56, maxWidth: 760 }}>
            <span style={{
              fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 600,
              letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--signal-400)',
            }}>How it works</span>
            <h2 style={{
              fontFamily: 'var(--font-display)', fontSize: 44, fontWeight: 600,
              color: 'var(--fg-bright)', letterSpacing: '0.01em', lineHeight: 1.08,
              margin: '12px 0 0',
            }}>From URL to cited answer in four stages.</h2>
          </div>
          <div style={{
            border: '1px solid var(--line-default)',
            borderRadius: 'var(--radius-xl)',
            overflow: 'hidden',
          }}>
            {STAGES.map((s, i) => (
              <div key={s.n} style={{
                display: 'grid',
                gridTemplateColumns: '72px 240px 1fr auto',
                gap: 24, alignItems: 'center',
                padding: '18px 24px',
                borderBottom: i < STAGES.length - 1 ? '1px solid var(--line-default)' : 'none',
                background: 'var(--bg-surface-2)',
                transition: 'background 150ms',
              }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--signal-400)', letterSpacing: '0.08em' }}>{s.n}</span>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 600, color: 'var(--fg-bright)', letterSpacing: '0.03em', textTransform: 'uppercase' }}>{s.stage}</span>
                <span style={{ fontSize: 13.5, color: 'var(--fg-muted)' }}>{s.desc}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)', whiteSpace: 'nowrap' }}>{s.tag}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Deploy CTA ── */}
      <section id="deploy" style={{
        position: 'relative',
        textAlign: 'center',
        padding: '96px 48px',
        background: 'var(--bg-surface-1)',
        borderTop: '1px solid var(--line-default)',
        borderBottom: '1px solid var(--line-default)',
        backgroundImage: 'var(--pattern-grid)',
        backgroundSize: 'var(--pattern-grid-size)',
      }}>
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', background: 'radial-gradient(ellipse at center, transparent, var(--bg-surface-1) 75%)' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h2 style={{
            fontFamily: 'var(--font-display)', fontSize: 52, fontWeight: 600,
            letterSpacing: '0.01em', color: 'var(--fg-bright)', lineHeight: 1.05, margin: 0,
          }}>One on-prem stack.<br />Zero data egress.</h2>
          <p style={{ color: 'var(--fg-muted)', fontSize: 18, margin: '20px 0 0' }}>
            Argus runs where your data already lives. Clone the repo and deploy in minutes.
          </p>
          <div style={{ marginTop: 32, display: 'inline-flex', gap: 12 }}>
            <a href="https://github.com/Chafficui/argus" target="_blank" rel="noopener noreferrer" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'linear-gradient(180deg, #2FBBD5, #0E7490)',
              color: '#031218',
              border: '1px solid rgba(34,211,238, 0.6)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 20px',
              fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 600,
              cursor: 'pointer', boxShadow: 'var(--glow-core)',
              textDecoration: 'none', transition: 'all 150ms',
            }}>
              Clone repository →
            </a>
            <a href="https://github.com/Chafficui/argus#readme" target="_blank" rel="noopener noreferrer" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '12px 20px',
              color: 'var(--fg-body)', fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 600,
              border: '1px solid var(--line-strong)', borderRadius: 'var(--radius-md)',
              background: 'transparent', textDecoration: 'none',
              transition: 'all 150ms',
            }}>
              Read the docs
            </a>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ padding: '48px 0 32px', borderTop: '1px solid var(--line-hairline)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 48px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <img src="/argus-logo.png" width={22} height={22} alt="" />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-subtle)' }}>
              argus · MIT license
            </span>
          </div>
          <div style={{ display: 'flex', gap: 24 }}>
            {[
              { label: 'GitHub', href: 'https://github.com/Chafficui/argus' },
              { label: 'Changelog', href: 'https://github.com/Chafficui/argus/blob/main/CHANGELOG.md' },
              { label: 'Security', href: 'https://github.com/Chafficui/argus/blob/main/SECURITY.md' },
            ].map((link) => (
              <a key={link.label} href={link.href} target="_blank" rel="noopener noreferrer" style={{
                fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 600,
                letterSpacing: '0.12em', textTransform: 'uppercase',
                color: 'var(--fg-muted)', textDecoration: 'none',
              }}>
                {link.label}
              </a>
            ))}
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes hero-breathe {
          0%, 100% { filter: drop-shadow(0 0 40px rgba(34,211,238,0.4)) drop-shadow(0 0 12px rgba(34,211,238,0.6)); }
          50%      { filter: drop-shadow(0 0 60px rgba(34,211,238,0.55)) drop-shadow(0 0 18px rgba(34,211,238,0.8)); }
        }
      `}</style>
    </div>
  )
}

function Cite({ n }: { n: number }) {
  return (
    <sup style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: 16, height: 16, borderRadius: 3,
      background: 'var(--signal-500-a10)', color: 'var(--signal-300)',
      border: '1px solid var(--signal-500-a20)',
      fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 600,
      margin: '0 2px', verticalAlign: 'super',
    }}>
      {n}
    </sup>
  )
}

import { useState, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatViews(n) {
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(1) + 'B'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return n.toLocaleString()
}

// ── Sub-components ───────────────────────────────────────────────────────────

function Header() {
  return (
    <header className="header">
      <div className="container">
        <div className="header__inner">
          <div className="header__logo">🔬</div>
          <span className="header__title">AI Content Research</span>
          <span className="header__subtitle">Powered by Ollama · 100% Local</span>
        </div>
      </div>
    </header>
  )
}

function SearchForm({ onSearch, loading }) {
  const [query, setQuery] = useState('')
  const [maxResults, setMaxResults] = useState(5)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim()) return
    onSearch(query.trim(), maxResults)
  }

  return (
    <section className="hero">
      <div className="container">
        <div className="hero__eyebrow">⚡ AI-Powered Research</div>
        <h1 className="hero__title">
          Analiza tendencias de<br /><span>YouTube con IA Local</span>
        </h1>
        <p className="hero__subtitle">
          Extrae videos, detecta patrones en títulos y descubre oportunidades de nicho
          usando Qwen3 14B + DeepSeek R1 8B, sin APIs comerciales.
        </p>

        <form className="search-form" onSubmit={handleSubmit}>
          <div className="search-input-wrapper">
            <input
              id="search-query"
              className="search-input"
              type="text"
              placeholder={`Ej: "Five Nights at Freddy's", "Minecraft survival 2024"...`}
              value={query}
              onChange={e => setQuery(e.target.value)}
              disabled={loading}
              autoComplete="off"
            />
            <div className="search-controls">
              <select
                id="max-results"
                className="max-results-select"
                value={maxResults}
                onChange={e => setMaxResults(Number(e.target.value))}
                disabled={loading}
              >
                {[5, 10, 15, 20].map(n => (
                  <option key={n} value={n}>{n} videos</option>
                ))}
              </select>
              <button
                id="analyze-btn"
                className="btn btn--primary"
                type="submit"
                disabled={loading || !query.trim()}
              >
                {loading ? '⏳ Analizando...' : '🚀 Analizar'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </section>
  )
}

function ProgressConsole({ messages, visible }) {
  if (!visible) return null
  return (
    <div className="container">
      <div className="console">
        <div className="console__header">
          <span className="console__dot console__dot--red" />
          <span className="console__dot console__dot--yellow" />
          <span className="console__dot console__dot--green" />
          <span className="console__title">research.log</span>
        </div>
        <div className="console__body">
          {messages.slice(0, -1).map((msg, i) => (
            <div key={i} className="console__line">✓ {msg}</div>
          ))}
          {messages.length > 0 && (
            <div className="console__line console__line--active">
              {messages[messages.length - 1]}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function VideosTable({ videos }) {
  if (!videos.length) return null
  return (
    <div>
      <h2 className="results-section__title">
        📹 Videos Extraídos
        <span style={{ fontSize: '14px', fontWeight: 400, color: 'var(--text-muted)' }}>
          ({videos.length} resultados)
        </span>
      </h2>
      <div className="videos-table-wrapper">
        <table className="videos-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Título</th>
              <th>Canal</th>
              <th>Vistas</th>
              <th>Duración</th>
              <th>Tipo</th>
            </tr>
          </thead>
          <tbody>
            {videos.map((v, i) => (
              <tr key={v.id}>
                <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                <td>
                  <div className="video-title">
                    <a href={v.url} target="_blank" rel="noreferrer">{v.title}</a>
                  </div>
                </td>
                <td>{v.channel || '—'}</td>
                <td>{formatViews(v.views)}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
                  {v.duration_text || '—'}
                </td>
                <td>
                  {v.is_short ? <span className="badge badge--short">#Short</span> : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function AnalysisCard({ icon, iconClass, label, model, content, loading }) {
  return (
    <div className="analysis-card">
      <div className="analysis-card__header">
        <div className={`analysis-card__icon ${iconClass}`}>{icon}</div>
        <div>
          <div className="analysis-card__label">{label}</div>
          <div className="analysis-card__model">{model}</div>
        </div>
      </div>
      {loading ? (
        <div>
          {[80, 60, 90, 50, 70].map((w, i) => (
            <div key={i} className={`skeleton skeleton-line ${w < 65 ? 'skeleton-line--short' : w < 75 ? 'skeleton-line--medium' : ''}`}
              style={{ width: `${w}%` }} />
          ))}
        </div>
      ) : content ? (
        <div className="analysis-content">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      ) : null}
    </div>
  )
}

// ── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [loading, setLoading]             = useState(false)
  const [consoleMessages, setConsole]     = useState([])
  const [videos, setVideos]               = useState([])
  const [titleAnalysis, setTitleAnalysis] = useState(null)
  const [trendAnalysis, setTrendAnalysis] = useState(null)
  const [titleLoading, setTitleLoading]   = useState(false)
  const [trendLoading, setTrendLoading]   = useState(false)
  const [error, setError]                 = useState(null)
  const [hasResults, setHasResults]       = useState(false)
  const abortRef = useRef(null)

  const addMsg = useCallback((msg) => {
    setConsole(prev => [...prev, msg])
  }, [])

  const handleSearch = useCallback(async (query, maxResults) => {
    // Reset state
    setLoading(true)
    setError(null)
    setVideos([])
    setTitleAnalysis(null)
    setTrendAnalysis(null)
    setConsole([])
    setHasResults(false)
    setTitleLoading(false)
    setTrendLoading(false)

    abortRef.current = new AbortController()

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: maxResults }),
        signal: abortRef.current.signal,
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // Parse SSE events
        const events = buffer.split('\n\n')
        buffer = events.pop() // keep incomplete last chunk

        for (const raw of events) {
          if (!raw.trim()) continue
          const lines = raw.split('\n')
          let event = 'message'
          let data = ''
          for (const line of lines) {
            if (line.startsWith('event: ')) event = line.slice(7)
            if (line.startsWith('data: '))  data  = line.slice(6)
          }
          if (!data) continue

          const payload = JSON.parse(data)

          if (event === 'progress') {
            addMsg(payload.message)
            if (payload.phase === 2) setTitleLoading(true)
            if (payload.phase === 3) { setTitleLoading(false); setTrendLoading(true) }
          }
          if (event === 'videos') {
            setVideos(payload.videos)
            setHasResults(true)
          }
          if (event === 'title_analysis') {
            setTitleLoading(false)
            setTitleAnalysis(payload.content)
          }
          if (event === 'trend_analysis') {
            setTrendLoading(false)
            setTrendAnalysis(payload.content)
          }
          if (event === 'done') {
            addMsg('✅ Análisis completado')
          }
          if (event === 'error') {
            setError(payload.message)
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(`Error de conexión con el servidor: ${err.message}`)
      }
    } finally {
      setLoading(false)
      setTitleLoading(false)
      setTrendLoading(false)
    }
  }, [addMsg])

  const showAnalysis = titleLoading || trendLoading || titleAnalysis || trendAnalysis

  return (
    <div className="app">
      <Header />
      <SearchForm onSearch={handleSearch} loading={loading} />
      <ProgressConsole messages={consoleMessages} visible={loading || consoleMessages.length > 0} />

      {error && (
        <div className="container">
          <div className="error-banner">
            ⚠️ {error}
          </div>
        </div>
      )}

      {hasResults && (
        <section className="results-section">
          <div className="container">
            <VideosTable videos={videos} />

            {showAnalysis && (
              <div>
                <h2 className="results-section__title">🧠 Análisis con IA</h2>
                <div className="analysis-grid">
                  <AnalysisCard
                    icon="🔤"
                    iconClass="analysis-card__icon--title"
                    label="Patrones de Títulos"
                    model="Qwen3 14B"
                    content={titleAnalysis}
                    loading={titleLoading}
                  />
                  <AnalysisCard
                    icon="📊"
                    iconClass="analysis-card__icon--trends"
                    label="Tendencias & Oportunidades"
                    model="DeepSeek R1 8B"
                    content={trendAnalysis}
                    loading={trendLoading}
                  />
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {!hasResults && !loading && !error && (
        <div className="container">
          <div className="empty-state">
            <div className="empty-state__icon">🔭</div>
            <div className="empty-state__title">Escribe un tema para empezar</div>
            <div className="empty-state__desc">
              El agente navegará YouTube automáticamente y analizará el mercado con IA local.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

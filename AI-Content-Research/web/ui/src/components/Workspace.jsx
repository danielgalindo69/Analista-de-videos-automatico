import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Icon } from './Icon'
import { formatPublished, formatViews, formatViewsPerDay, getFriendlyError } from '../utils/formatters'

function SkeletonText() {
  return <div className="skeleton-copy" aria-label="Generando análisis">{[92, 72, 84, 55, 78].map((width) => <span key={width} style={{ width: `${width}%` }} />)}</div>
}

export function PipelineCard({ info, status }) {
  const extractionModel = info.extraction_model || 'Qwen3 14B'
  const reasoningModel = info.reasoning_model || 'DeepSeek R1 8B'
  const extractionProvider = info.extraction_provider_name || 'Ollama'
  const reasoningProvider = info.reasoning_provider_name || 'Ollama'
  const providerLabel = info.provider_label || 'Ollama'
  const isLocal = info.processing_local !== false
  return (
    <aside className="pipeline-card" aria-label="Configuración del análisis">
      <div className="pipeline-card__header">
        <div><span className="section-kicker">Motor activo</span><h2>Flujo de análisis local</h2></div>
        <span className={`provider-chip provider-chip--${status}`}><Icon name={isLocal ? 'server' : 'cloud'} size={15} /> {providerLabel}</span>
      </div>
      <ol className="pipeline">
        <li><span className="pipeline__index">01</span><span><strong>Explorar</strong><small>Metadatos públicos de YouTube</small></span><Icon name="youtube" size={19} /></li>
        <li><span className="pipeline__index">02</span><span><strong>Leer patrones</strong><small>{extractionProvider} · {extractionModel}</small></span><Icon name="brain" size={19} /></li>
        <li><span className="pipeline__index">03</span><span><strong>Detectar oportunidades</strong><small>{reasoningProvider} · {reasoningModel}</small></span><Icon name="trend" size={19} /></li>
      </ol>
      <div className="privacy-note"><Icon name={isLocal ? 'lock' : 'cloud'} size={16} /> {isLocal ? 'Tus datos y prompts permanecen en este equipo.' : 'Los prompts se enviarán a los proveedores cloud seleccionados.'}</div>
    </aside>
  )
}

export function ProgressPanel({ messages }) {
  if (!messages.length) return null
  return (
    <section className="progress-panel" aria-live="polite">
      <div className="progress-panel__indicator"><span /><span /><span /></div>
      <div><span className="section-kicker">Análisis en curso</span><p>{messages.at(-1)}</p></div>
      <span className="progress-panel__count">Paso {Math.min(messages.length, 3)} de 3</span>
    </section>
  )
}

export function ErrorNotice({ error }) {
  if (!error) return null
  const friendly = getFriendlyError(error)
  return (
    <section className="error-notice" role="alert">
      <span className="error-notice__icon">!</span>
      <div>
        <h2>{friendly.title}</h2><p>{friendly.description}</p>
        {friendly.detail && <details><summary>Ver detalle técnico</summary><code>{friendly.detail}</code></details>}
      </div>
    </section>
  )
}

export function VideosTable({ videos }) {
  if (!videos.length) return null
  return (
    <section className="results-block">
      <div className="results-heading">
        <div><span className="section-kicker">Muestra analizada</span><h2>Videos encontrados</h2></div>
        <span className="result-total">{videos.length} resultados</span>
      </div>
      <div className="videos-table-wrap">
        <table className="videos-table">
          <thead><tr><th>Título</th><th>Canal</th><th>Publicado</th><th>Vistas</th><th>Vistas/día</th><th>Duración</th><th><span className="sr-only">Abrir</span></th></tr></thead>
          <tbody>
            {videos.map((video) => (
              <tr key={video.id}>
                <td data-label="Título">
                  <a className="video-title" href={video.url} target="_blank" rel="noreferrer">
                    <span className="video-title__icon"><Icon name={video.is_short ? 'play' : 'film'} size={17} /></span>
                    <span>{video.title}{video.is_short && <small>Short</small>}</span>
                  </a>
                </td>
                <td data-label="Canal">{video.channel || 'Sin canal'}</td>
                <td data-label="Publicado" className="number-cell">{formatPublished(video)}</td>
                <td data-label="Vistas" className="number-cell">{formatViews(video.views)}</td>
                <td data-label="Vistas por día" className="number-cell velocity-cell">{formatViewsPerDay(video.views_per_day)}</td>
                <td data-label="Duración" className="number-cell">{video.duration_text || '—'}</td>
                <td><a className="external-link" href={video.url} target="_blank" rel="noreferrer" aria-label={`Abrir ${video.title}`}><Icon name="external" size={17} /></a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function AnalysisCard({ eyebrow, title, model, icon, content, loading, tone }) {
  if (!content && !loading) return null
  return (
    <article className={`analysis-card analysis-card--${tone}`}>
      <header className="analysis-card__header">
        <span className="analysis-card__icon"><Icon name={icon} size={21} /></span>
        <div><span className="section-kicker">{eyebrow}</span><h3>{title}</h3></div>
        <span className="model-tag">{model}</span>
      </header>
      {loading ? <SkeletonText /> : <div className="analysis-content"><ReactMarkdown>{content}</ReactMarkdown></div>}
    </article>
  )
}

export function ReportWorkspace({ videos, info, titleAnalysis, trendAnalysis, titleLoading, trendLoading }) {
  const [activeTab, setActiveTab] = useState('videos')
  const tabs = [
    { id: 'videos', label: 'Videos', icon: 'film', available: videos.length > 0 },
    { id: 'titles', label: 'Patrones de títulos', icon: 'spark', available: titleLoading || Boolean(titleAnalysis) },
    { id: 'trends', label: 'Oportunidades', icon: 'trend', available: trendLoading || Boolean(trendAnalysis) },
  ]

  return (
    <section className="report-workspace" aria-label="Resultados de la investigación">
      <div className="results-heading report-workspace__heading">
        <div><span className="section-kicker">Investigación completa</span><h2>Explora el reporte por secciones</h2></div>
        <span className="result-total">{videos.length} videos analizados</span>
      </div>

      <div className="report-tabs" role="tablist" aria-label="Secciones del reporte">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`report-tab-${tab.id}`}
            className={`report-tab ${activeTab === tab.id ? 'report-tab--active' : ''}`}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`report-panel-${tab.id}`}
            disabled={!tab.available}
            onClick={() => setActiveTab(tab.id)}
          >
            <Icon name={tab.icon} size={15} />
            {tab.label}
            {!tab.available && <span className="report-tab__pending">Pendiente</span>}
          </button>
        ))}
      </div>

      <div
        id={`report-panel-${activeTab}`}
        className={`report-panel ${activeTab === 'videos' ? '' : 'report-reading-pane'}`}
        role="tabpanel"
        aria-labelledby={`report-tab-${activeTab}`}
        tabIndex={0}
      >
        {activeTab === 'videos' && <VideosTable videos={videos} />}
        {activeTab === 'titles' && (
          <AnalysisCard eyebrow="Lenguaje" title="Patrones de títulos" model={info.extraction_model || 'Qwen3 14B'} icon="spark" content={titleAnalysis} loading={titleLoading} tone="amber" />
        )}
        {activeTab === 'trends' && (
          <AnalysisCard eyebrow="Mercado" title="Tendencias y oportunidades" model={info.reasoning_model || 'DeepSeek R1 8B'} icon="trend" content={trendAnalysis} loading={trendLoading} tone="blue" />
        )}
      </div>
    </section>
  )
}

export function EmptyState() {
  return (
    <section className="empty-guide">
      <div className="empty-guide__intro"><span className="section-kicker">Tu primer reporte</span><h2>De una idea amplia a una oportunidad concreta.</h2></div>
      <div className="empty-guide__steps">
        <div><span>01</span><strong>Define el territorio</strong><p>Escribe un tema, nicho o tipo de audiencia.</p></div>
        <div><span>02</span><strong>Contrasta el mercado</strong><p>El agente estudia videos y señales de rendimiento.</p></div>
        <div><span>03</span><strong>Decide con evidencia</strong><p>Recibe patrones de títulos y espacios por explorar.</p></div>
      </div>
    </section>
  )
}

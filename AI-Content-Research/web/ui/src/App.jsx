import { Header } from './components/Header'
import { ResearchForm } from './components/ResearchForm'
import { AnalysisResults, EmptyState, ErrorNotice, PipelineCard, ProgressPanel, VideosTable } from './components/Workspace'
import { Icon } from './components/Icon'
import { useAnalysisStream } from './hooks/useAnalysisStream'
import { useSystemInfo } from './hooks/useSystemInfo'

export default function App() {
  const system = useSystemInfo()
  const analysis = useAnalysisStream()

  return (
    <div className="app">
      <Header status={system.status} />
      <main id="main">
        <section className="research-hero">
          <div className="shell research-hero__grid">
            <div className="research-hero__content">
              <div className="eyebrow"><Icon name="spark" size={16} /> Inteligencia de contenido para creadores</div>
              <h1>Encuentra el ángulo que otros todavía no ven.</h1>
              <p>Investiga un nicho de YouTube, identifica patrones de alto rendimiento y convierte señales del mercado en decisiones de contenido.</p>
              <ResearchForm loading={analysis.loading} onCancel={analysis.cancel} onSearch={analysis.analyze} />
            </div>
            <PipelineCard info={system.info} status={system.status} />
          </div>
        </section>

        <div className="shell workspace">
          <ProgressPanel messages={analysis.loading ? analysis.messages : []} />
          <ErrorNotice error={analysis.error} />
          {analysis.hasResults ? (
            <>
              <VideosTable videos={analysis.videos} />
              <AnalysisResults info={system.info} titleAnalysis={analysis.titleAnalysis} trendAnalysis={analysis.trendAnalysis} titleLoading={analysis.titleLoading} trendLoading={analysis.trendLoading} />
            </>
          ) : !analysis.loading && !analysis.error ? <EmptyState /> : null}
        </div>
      </main>

      <footer className="footer">
        <div className="shell footer__inner"><span>AI Content Research</span><span><Icon name="lock" size={14} /> Privado por diseño · Procesamiento local</span></div>
      </footer>
    </div>
  )
}

import { Icon } from './Icon'

export function Header({ status }) {
  const statusLabel = status === 'online' ? 'Sistema listo' : status === 'checking' ? 'Verificando' : 'Sin conexión'

  return (
    <header className="topbar">
      <div className="shell topbar__inner">
        <a className="brand" href="#main" aria-label="AI Content Research, inicio">
          <span className="brand__mark"><Icon name="activity" size={21} /></span>
          <span><strong>Content Research</strong><small>Intelligence workspace</small></span>
        </a>
        <div className={`system-status system-status--${status}`} title="Estado del backend local">
          <span className="system-status__dot" />
          <span>{statusLabel}</span>
          <span className="system-status__provider">Ollama · Local</span>
        </div>
      </div>
    </header>
  )
}

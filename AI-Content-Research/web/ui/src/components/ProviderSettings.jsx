import { useEffect, useMemo, useState } from 'react'
import { Icon } from './Icon'

const EMPTY_ROUTES = {
  extraction: { provider_id: 'ollama', model: '' },
  reasoning: { provider_id: 'ollama', model: '' },
}

async function readJson(response) {
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || 'No se pudo completar la operación.')
  return payload
}

export function ProviderSettings({ open, onClose, onSaved }) {
  const [providers, setProviders] = useState([])
  const [routes, setRoutes] = useState(EMPTY_ROUTES)
  const [models, setModels] = useState({})
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  const configuredProviders = useMemo(
    () => providers.filter((provider) => provider.configured),
    [providers],
  )

  useEffect(() => {
    if (!open) {
      setApiKey('')
      setShowKey(false)
      setMessage(null)
      return
    }

    let active = true
    setLoading(true)
    fetch('/api/providers')
      .then(readJson)
      .then(async (payload) => {
        if (!active) return
        setProviders(payload.providers)
        setRoutes(payload.routes)
        const configured = payload.providers.filter((provider) => provider.configured)
        const entries = await Promise.all(configured.map(async (provider) => {
          try {
            const response = await fetch(`/api/providers/${provider.id}/models`)
            const data = await readJson(response)
            return [provider.id, data.models]
          } catch {
            return [provider.id, []]
          }
        }))
        if (active) setModels(Object.fromEntries(entries))
      })
      .catch((error) => active && setMessage({ tone: 'error', text: error.message }))
      .finally(() => active && setLoading(false))

    return () => { active = false }
  }, [open])

  if (!open) return null

  const connectGemini = async () => {
    if (!apiKey.trim()) return
    setLoading(true)
    setMessage(null)
    try {
      const response = await fetch('/api/providers/gemini/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey.trim() }),
      })
      const payload = await readJson(response)
      setModels((current) => ({ ...current, gemini: payload.models }))
      setProviders((current) => current.map((provider) => (
        provider.id === 'gemini' ? { ...provider, configured: true } : provider
      )))
      setApiKey('')
      setMessage({ tone: 'success', text: `Gemini conectado. ${payload.models.length} modelos disponibles.` })
    } catch (error) {
      setMessage({ tone: 'error', text: error.message })
    } finally {
      setLoading(false)
    }
  }

  const disconnectGemini = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const response = await fetch('/api/providers/gemini/credential', { method: 'DELETE' })
      const payload = await readJson(response)
      setProviders((current) => current.map((provider) => (
        provider.id === 'gemini' ? { ...provider, configured: payload.configured } : provider
      )))
      if (!payload.configured) setModels((current) => ({ ...current, gemini: [] }))
      setRoutes(payload.routes)
      setMessage({
        tone: 'success',
        text: payload.configured
          ? 'Se eliminó la clave de sesión. Gemini continúa activo mediante la variable de entorno del servidor.'
          : 'La credencial de Gemini fue eliminada de esta sesión.',
      })
      await onSaved()
    } catch (error) {
      setMessage({ tone: 'error', text: error.message })
    } finally {
      setLoading(false)
    }
  }

  const changeProvider = async (task, providerId) => {
    let providerModels = models[providerId] || []
    if (!providerModels.length) {
      try {
        const response = await fetch(`/api/providers/${providerId}/models`)
        const payload = await readJson(response)
        providerModels = payload.models
        setModels((current) => ({ ...current, [providerId]: providerModels }))
      } catch (error) {
        setMessage({ tone: 'error', text: error.message })
      }
    }
    setRoutes((current) => ({
      ...current,
      [task]: { provider_id: providerId, model: providerModels[0]?.id || '' },
    }))
  }

  const saveRoutes = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const response = await fetch('/api/providers/configuration/routes', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(routes),
      })
      const payload = await readJson(response)
      setRoutes(payload.routes)
      setMessage({ tone: 'success', text: 'Configuración aplicada a esta sesión.' })
      await onSaved()
    } catch (error) {
      setMessage({ tone: 'error', text: error.message })
    } finally {
      setLoading(false)
    }
  }

  const gemini = providers.find((provider) => provider.id === 'gemini')

  return (
    <div className="settings-overlay" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="settings-panel" role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <header className="settings-panel__header">
          <div><span className="section-kicker">Configuración de IA</span><h2 id="settings-title">Proveedores y modelos</h2></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Cerrar configuración"><Icon name="close" size={18} /></button>
        </header>

        <div className="settings-panel__body">
          <div className="settings-security-note"><Icon name="lock" size={15} /><span>Las API keys viven sólo en la memoria del backend y se eliminan al reiniciar Docker.</span></div>

          <section className="provider-section">
            <div className="provider-section__title"><div><span className="section-kicker">Conexiones</span><h3>Proveedores disponibles</h3></div></div>
            <div className="provider-cards">
              {providers.map((provider) => (
                <article className={`provider-card ${provider.configured ? 'provider-card--ready' : ''}`} key={provider.id}>
                  <span className="provider-card__icon"><Icon name={provider.is_local ? 'server' : 'cloud'} size={18} /></span>
                  <div><strong>{provider.name}</strong><small>{provider.is_local ? 'Procesamiento local' : 'Procesamiento en la nube'}</small></div>
                  <span className="provider-card__state">{provider.configured ? 'Disponible' : 'Sin configurar'}</span>
                </article>
              ))}
            </div>

            {gemini && !gemini.configured ? (
              <div className="credential-form">
                <label htmlFor="gemini-key">Gemini API key</label>
                <div className="credential-field">
                  <Icon name="key" size={16} />
                  <input id="gemini-key" type={showKey ? 'text' : 'password'} value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="Pega tu clave de Google AI Studio" autoComplete="off" />
                  <button type="button" onClick={() => setShowKey((value) => !value)} aria-label={showKey ? 'Ocultar API key' : 'Mostrar API key'}><Icon name={showKey ? 'eyeOff' : 'eye'} size={16} /></button>
                </div>
                <button className="button button--secondary" type="button" onClick={connectGemini} disabled={loading || !apiKey.trim()}>Probar y conectar Gemini</button>
              </div>
            ) : gemini?.configured ? (
              <button className="text-button text-button--danger" type="button" onClick={disconnectGemini} disabled={loading}>Desconectar Gemini de esta sesión</button>
            ) : null}
          </section>

          <section className="provider-section">
            <div className="provider-section__title"><div><span className="section-kicker">Enrutamiento</span><h3>Modelo por tipo de trabajo</h3></div></div>
            {[
              ['extraction', 'Títulos y patrones', 'Clasificación y lectura de lenguaje'],
              ['reasoning', 'Tendencias y oportunidades', 'Razonamiento estratégico del mercado'],
            ].map(([task, label, description]) => (
              <div className="route-row" key={task}>
                <div><strong>{label}</strong><small>{description}</small></div>
                <select value={routes[task].provider_id} onChange={(event) => changeProvider(task, event.target.value)} disabled={loading} aria-label={`Proveedor para ${label}`}>
                  {configuredProviders.map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}
                </select>
                <select value={routes[task].model} onChange={(event) => setRoutes((current) => ({ ...current, [task]: { ...current[task], model: event.target.value } }))} disabled={loading || !(models[routes[task].provider_id] || []).length} aria-label={`Modelo para ${label}`}>
                  {(models[routes[task].provider_id] || []).map((model) => <option key={model.id} value={model.id}>{model.name}</option>)}
                </select>
              </div>
            ))}
          </section>

          {message && <div className={`settings-message settings-message--${message.tone}`} role="status">{message.tone === 'success' && <Icon name="check" size={14} />}{message.text}</div>}
        </div>

        <footer className="settings-panel__footer">
          <button className="button button--secondary" type="button" onClick={onClose}>Cerrar</button>
          <button className="button button--primary" type="button" onClick={saveRoutes} disabled={loading || !routes.extraction.model || !routes.reasoning.model}>Aplicar configuración</button>
        </footer>
      </section>
    </div>
  )
}

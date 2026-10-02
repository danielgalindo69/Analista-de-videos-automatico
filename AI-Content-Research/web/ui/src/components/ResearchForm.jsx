import { useState } from 'react'
import { Icon } from './Icon'

const EXAMPLES = ['Finanzas para jóvenes', 'Videojuegos de terror', 'Productividad con IA']

export function ResearchForm({ loading, onCancel, onSearch }) {
  const [query, setQuery] = useState('')
  const [maxResults, setMaxResults] = useState(5)

  const submit = (event) => {
    event.preventDefault()
    if (!query.trim() || loading) return
    onSearch(query.trim(), maxResults)
  }

  return (
    <form className="research-form" onSubmit={submit}>
      <label className="research-form__label" htmlFor="search-query">Tema o nicho a investigar</label>
      <div className="research-form__field">
        <Icon name="search" size={20} />
        <input id="search-query" type="search" placeholder="Ej. Historias de terror, hábitos financieros..." value={query} onChange={(event) => setQuery(event.target.value)} disabled={loading} autoComplete="off" />
      </div>

      <div className="research-form__actions">
        <label className="result-count" htmlFor="max-results">
          <span>Profundidad</span>
          <select id="max-results" value={maxResults} onChange={(event) => setMaxResults(Number(event.target.value))} disabled={loading}>
            {[5, 10, 15, 20].map((count) => <option key={count} value={count}>{count} videos</option>)}
          </select>
        </label>

        {loading ? (
          <button className="button button--secondary" type="button" onClick={onCancel}><Icon name="close" size={17} /> Cancelar</button>
        ) : (
          <button className="button button--primary" type="submit" disabled={!query.trim()}>Analizar mercado <Icon name="play" size={17} /></button>
        )}
      </div>

      <div className="research-form__examples" aria-label="Ejemplos de búsqueda">
        <span>Prueba con</span>
        {EXAMPLES.map((example) => <button key={example} type="button" onClick={() => setQuery(example)} disabled={loading}>{example}</button>)}
      </div>
    </form>
  )
}

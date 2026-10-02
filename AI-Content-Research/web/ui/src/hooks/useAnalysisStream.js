import { useCallback, useRef, useState } from 'react'

const INITIAL_STATE = {
  loading: false,
  messages: [],
  videos: [],
  titleAnalysis: null,
  trendAnalysis: null,
  titleLoading: false,
  trendLoading: false,
  error: null,
  hasResults: false,
}

export function useAnalysisStream() {
  const [state, setState] = useState(INITIAL_STATE)
  const abortRef = useRef(null)
  const update = useCallback((partial) => setState((current) => ({ ...current, ...partial })), [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    update({ loading: false, titleLoading: false, trendLoading: false })
  }, [update])

  const analyze = useCallback(async (query, maxResults) => {
    abortRef.current?.abort()
    abortRef.current = new AbortController()
    setState({ ...INITIAL_STATE, loading: true })

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: maxResults }),
        signal: abortRef.current.signal,
      })
      if (!response.ok || !response.body) throw new Error(`El servidor respondió con el estado ${response.status}.`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const rawEvent of events) {
          if (!rawEvent.trim()) continue
          let event = 'message'
          let data = ''
          for (const line of rawEvent.split('\n')) {
            if (line.startsWith('event: ')) event = line.slice(7)
            if (line.startsWith('data: ')) data += line.slice(6)
          }
          if (!data) continue

          const payload = JSON.parse(data)
          setState((current) => {
            if (event === 'progress') return { ...current, messages: [...current.messages, payload.message], titleLoading: payload.phase === 2, trendLoading: payload.phase === 3 }
            if (event === 'videos') return { ...current, videos: payload.videos, hasResults: true }
            if (event === 'title_analysis') return { ...current, titleAnalysis: payload.content, titleLoading: false }
            if (event === 'trend_analysis') return { ...current, trendAnalysis: payload.content, trendLoading: false }
            if (event === 'done') return { ...current, messages: [...current.messages, 'Análisis completado'] }
            if (event === 'error') return { ...current, error: payload.message }
            return current
          })
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') update({ error: `Error de conexión con el servidor: ${error.message}` })
    } finally {
      setState((current) => ({ ...current, loading: false, titleLoading: false, trendLoading: false }))
    }
  }, [update])

  return { ...state, analyze, cancel }
}

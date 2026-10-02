import { useEffect, useState } from 'react'

const DEFAULT_INFO = { extraction_model: 'Qwen3 14B', reasoning_model: 'DeepSeek R1 8B' }

export function useSystemInfo() {
  const [state, setState] = useState({ info: DEFAULT_INFO, status: 'checking' })

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/info', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error('Backend no disponible')
        return response.json()
      })
      .then((info) => setState({ info, status: 'online' }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ info: DEFAULT_INFO, status: 'offline' })
      })
    return () => controller.abort()
  }, [])

  return state
}

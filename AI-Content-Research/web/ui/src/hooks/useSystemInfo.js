import { useCallback, useEffect, useState } from 'react'

const DEFAULT_INFO = { extraction_model: 'Qwen3 14B', reasoning_model: 'DeepSeek R1 8B' }

export function useSystemInfo() {
  const [state, setState] = useState({ info: DEFAULT_INFO, status: 'checking' })

  const refresh = useCallback(async (signal) => {
    try {
      const response = await fetch('/api/info', { signal })
      if (!response.ok) throw new Error('Backend no disponible')
      const info = await response.json()
      setState({ info, status: 'online' })
      return info
    } catch (error) {
      if (error.name !== 'AbortError') setState({ info: DEFAULT_INFO, status: 'offline' })
      return null
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    refresh(controller.signal)
    return () => controller.abort()
  }, [refresh])

  return { ...state, refresh: () => refresh(undefined) }
}

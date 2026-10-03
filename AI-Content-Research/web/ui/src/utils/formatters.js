export function formatViews(value) {
  const views = Number(value) || 0
  return new Intl.NumberFormat('es-CO', {
    notation: views >= 1_000 ? 'compact' : 'standard',
    maximumFractionDigits: 1,
  }).format(views)
}

export function formatViewsPerDay(value) {
  if (value === null || value === undefined) return '—'
  return `${formatViews(value)}/día`
}

export function formatPublished(video) {
  if (!video.published_at) return video.published_text || '—'

  const elapsedSeconds = Math.max(0, (Date.now() - new Date(video.published_at).getTime()) / 1_000)
  const ranges = [
    ['year', 31_536_000],
    ['month', 2_592_000],
    ['week', 604_800],
    ['day', 86_400],
    ['hour', 3_600],
    ['minute', 60],
  ]
  const formatter = new Intl.RelativeTimeFormat('es', { numeric: 'auto' })

  for (const [unit, seconds] of ranges) {
    if (elapsedSeconds >= seconds) {
      return formatter.format(-Math.max(1, Math.round(elapsedSeconds / seconds)), unit)
    }
  }
  return 'ahora'
}

export function getFriendlyError(error) {
  const message = error || 'Ocurrió un error inesperado.'
  const normalized = message.toLowerCase()

  if (normalized.includes('cuda') || message.includes('0xc0000409')) {
    return {
      title: 'Ollama se detuvo por un error de GPU',
      description: 'Reinicia Ollama y vuelve a intentarlo. Si continúa, reduce la cantidad de videos o ejecuta el modelo en CPU.',
      detail: message,
    }
  }

  if (normalized.includes('timed out') || normalized.includes('timeout')) {
    return {
      title: 'El modelo tardó demasiado en responder',
      description: 'Prueba con menos videos o reinicia Ollama antes de repetir el análisis.',
    }
  }

  return { title: 'No pudimos completar el análisis', description: message }
}

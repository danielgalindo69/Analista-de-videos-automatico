# Plan de implementación local

## Objetivo de producto

Convertir una consulta amplia en una decisión de contenido respaldada por evidencia. El flujo debe ayudar al creador a entender qué funciona, por qué funciona y qué ángulo puede ejecutar, manteniendo el procesamiento local como opción principal.

## Principios

- Entregas verticales: cada fase debe producir valor visible desde la interfaz.
- Evidencia antes que opinión: cada recomendación debe poder rastrearse hasta videos concretos.
- Los datos desconocidos se muestran como desconocidos; no se estiman silenciosamente.
- El frontend consume contratos estables y no conoce detalles de Ollama ni de futuros proveedores.
- La arquitectura local debe poder evolucionar sin introducir infraestructura cloud antes de necesitarla.

## Fase 1 — Señales de rendimiento confiables

**Objetivo:** distinguir popularidad acumulada de crecimiento reciente.

- [x] Extraer antigüedad de publicación desde los resultados de YouTube.
- [x] Conservar el texto original y una fecha estimada normalizada.
- [x] Calcular vistas por día cuando exista información suficiente.
- [x] Mostrar fecha y velocidad en la interfaz.
- [x] Enviar las nuevas señales a los analizadores.
- [ ] Validar la fecha exacta visitando el video o mediante YouTube Data API.
- [ ] Añadir una puntuación de confianza por campo extraído.

**Criterio de salida:** el usuario puede diferenciar un video antiguo con muchas vistas de uno reciente que está creciendo con rapidez.

## Fase 2 — Resultado accionable

**Objetivo:** transformar el análisis en un brief utilizable.

- Crear un modelo estructurado `ContentBrief`.
- Generar audiencia, necesidad, ángulo, hipótesis, títulos, esquema y CTA.
- Relacionar cada recomendación con sus videos de evidencia.
- Permitir copiar o exportar el brief como Markdown.
- Separar datos calculados por el sistema de conclusiones generadas por el LLM.

**Criterio de salida:** una investigación puede convertirse en un brief guardable sin volver a escribir el contexto.

## Fase 3 — Biblioteca local

**Objetivo:** hacer que las investigaciones acumulen valor.

- Introducir SQLite con repositorios desacoplados del almacenamiento.
- Guardar consulta, filtros, videos, análisis, brief, modelos y fecha.
- Listar, abrir, renombrar y eliminar investigaciones.
- Repetir una investigación y comparar sus cambios.
- Definir versión de esquema y migraciones desde el inicio.

**Criterio de salida:** cerrar o reiniciar la aplicación no elimina el historial y dos ejecuciones pueden compararse.

## Fase 4 — Proveedores intercambiables

**Objetivo:** elegir privacidad, velocidad o calidad sin cambiar el flujo.

- Definir `LLMProvider` y sacar la ejecución concreta del router de tareas.
- Implementar Ollama como primer adaptador.
- Añadir validación de conexión y listado de modelos.
- Añadir un segundo proveedor para validar la abstracción.
- Guardar secretos fuera del navegador y nunca incluirlos en logs.
- Mostrar proveedor, modelo, privacidad y costo estimado antes de ejecutar.

**Criterio de salida:** cambiar de proveedor no modifica analizadores, prompts ni componentes de resultados.

## Fase 5 — Comparación y radar

**Objetivo:** descubrir cambios y oportunidades, no sólo producir reportes aislados.

- Comparar consultas, idiomas o ventanas temporales.
- Crear listas de seguimiento de nichos y competidores.
- Ejecutar actualizaciones manuales antes de automatizar horarios.
- Destacar cambios materiales y evitar notificaciones sin novedad.
- Incorporar rendimiento real de videos publicados como retroalimentación.

## Trabajo transversal

### Calidad

- Pruebas unitarias para parsers, cálculos y serializadores.
- Fixtures HTML para detectar cambios en el DOM de YouTube.
- Estados vacíos, parciales y de error diferenciados.
- Registrar versión de prompt y modelo en cada resultado.

### Límites locales iniciales

- Un análisis activo a la vez.
- Entre 5 y 20 videos por investigación desde la UI.
- Tiempo máximo configurable para navegador y modelos.
- Cancelación explícita desde la UI.
- Caché de consultas repetidas después de incorporar la biblioteca local.

### Métricas de producto

- Investigaciones completadas.
- Porcentaje convertido en brief.
- Briefs guardados o exportados.
- Consultas repetidas y comparadas.
- Tiempo por etapa y tasa de extracción incompleta.

## Siguiente entrega recomendada

Completar la Fase 1 con fixtures reales de YouTube y, a continuación, implementar `ContentBrief` como contrato estructurado. No conviene introducir autenticación, colas o servicios cloud mientras el flujo local principal todavía se está validando.

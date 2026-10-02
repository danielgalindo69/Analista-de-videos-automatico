# Dirección de producto

## Propuesta central

AI Content Research debe convertirse en un espacio de decisión para creadores: pasar de una idea amplia a un brief de contenido respaldado por señales reales del mercado, sin obligar al usuario a comprender modelos, prompts o infraestructura.

La promesa diferencial combina tres principios:

1. **Privacidad local por defecto.** Ollama funciona sin enviar la investigación fuera del equipo.
2. **Libertad de proveedor.** El usuario puede elegir velocidad, privacidad, costo o calidad sin cambiar su flujo de trabajo.
3. **Evidencia antes que generación.** La aplicación investiga el mercado antes de proponer títulos, formatos o guiones.

## Evolución recomendada del flujo

### 1. Investigación

El flujo actual analiza una consulta y entrega videos, patrones de títulos y oportunidades. Es el núcleo correcto y debe seguir siendo la primera acción del producto.

### 2. Brief accionable

El siguiente paso debería transformar los hallazgos en un brief con:

- audiencia y necesidad detectada;
- ángulo recomendado y razón;
- tres títulos con hipótesis de clic;
- estructura del video;
- riesgos de saturación o falta de evidencia;
- referencias de los videos que sustentan la recomendación.

### 3. Biblioteca de investigaciones

Guardar consultas, resultados y briefs permite comparar nichos, reutilizar evidencia y medir cómo evoluciona una oportunidad. La biblioteca debe almacenar datos localmente primero.

### 4. Seguimiento

Una investigación puede convertirse en un radar que se actualiza bajo demanda. Antes de automatizarlo, conviene validar que los usuarios realmente regresan a comparar el mismo nicho.

## Arquitectura multi-proveedor

El frontend no debería conocer SDKs ni secretos. El backend debe exponer una interfaz estable y resolver allí el proveedor activo.

```python
class LLMProvider(Protocol):
    id: str
    capabilities: set[str]

    async def health(self) -> ProviderHealth: ...
    async def list_models(self) -> list[ModelInfo]: ...
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
```

Proveedores iniciales recomendados:

- `OllamaProvider`: privado y sin costo por token.
- `GeminiProvider`: alternativa accesible para equipos modestos.
- `OpenAIProvider`: buena calidad general y salidas estructuradas.
- `AnthropicProvider`: análisis extenso y razonamiento editorial.

La configuración debería separar `provider`, `model` y `task`. Así el usuario puede usar un modelo económico para extraer patrones y otro más capaz para razonar oportunidades. Las API keys deben permanecer en variables de entorno o almacenamiento seguro del sistema, nunca en el navegador ni en archivos versionados.

## Orden sugerido de implementación

1. Adaptador común de proveedores y endpoint de estado/modelos.
2. Pantalla de configuración con validación de conexión antes de guardar.
3. Persistencia local de investigaciones.
4. Generación de brief a partir de un análisis existente.
5. Comparación de dos nichos o consultas.
6. Seguimiento periódico sólo después de validar uso recurrente.

## Métrica principal

Medir cuántas investigaciones terminan en un brief guardado o exportado. Esto refleja una decisión de contenido real mejor que contar búsquedas, tokens o tiempo dentro de la aplicación.

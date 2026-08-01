# AI Content Research Framework

Framework de investigación automática de contenido digital.
Navega plataformas, extrae datos y analiza tendencias usando modelos LLM locales vía Ollama.

---

## Requisitos

- Python 3.11+
- [Ollama](https://ollama.com/) corriendo en `localhost:11434`
- Modelos descargados:
  ```bash
  ollama pull qwen3:14b
  ollama pull deepseek-r1:8b
  ```
- Playwright con Chromium:
  ```bash
  playwright install chromium
  ```

---

## Instalación

```bash
# 1. Clonar o descargar el proyecto
cd "AI-Content-Research"

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar browsers de Playwright
playwright install chromium

# 5. Configurar variables de entorno
copy .env.example .env
# Editar .env si tus valores difieren de los defaults
```

---

## Estructura del Proyecto

```
AI-Content-Research/
│
├── core/                          # Contratos y modelos — cero dependencias externas
│   ├── interfaces/
│   │   ├── base_platform.py       # ABC: contrato de toda plataforma
│   │   ├── base_analyzer.py       # ABC: contrato de todo analizador
│   │   └── base_reporter.py       # ABC: contrato de todo reporte
│   ├── models/
│   │   ├── llm.py                 # TaskType, LLMRequest, LLMResponse
│   │   ├── content.py             # Platform, ContentItem
│   │   └── analysis.py            # AnalysisRequest, AnalysisResult, Finding
│   └── exceptions/
│       └── framework.py           # Jerarquía completa de excepciones
│
├── infrastructure/                # Implementaciones concretas de servicios
│   ├── browser/
│   │   └── playwright_manager.py  # Chromium async context manager
│   ├── llm/
│   │   ├── ollama_client.py       # Cliente HTTP async para Ollama
│   │   └── router.py              # LLMRouter: selección de modelo por TaskType
│   ├── storage/
│   │   └── file_storage.py        # Persistencia JSON + Markdown
│   └── logging/
│       └── setup.py               # Configuración centralizada de Loguru
│
├── prompts/                       # Sistema de prompts versionado
│   ├── registry.py                # Carga y cachea templates en memoria
│   └── templates/
│       └── system_base.md         # Prompt base del sistema
│
├── platforms/                     # Módulos por plataforma
│   └── base/
│       └── platform_base.py       # Base concreta con DI de infraestructura
│
├── config/
│   └── settings.py                # Pydantic Settings — lee .env
│
├── .env.example                   # Template de configuración
└── requirements.txt
```

---

## Modelos y Routing

| TaskType | Modelo |
|---|---|
| `EXTRACTION`, `CLASSIFICATION`, `SUMMARIZATION` | `qwen3:14b` |
| `TOOL_CALLING`, `COMPARISON`, `REPORT_GENERATION` | `qwen3:14b` |
| `REASONING`, `PATTERN_DETECTION` | `deepseek-r1:8b` |
| `HYPOTHESIS_VALIDATION`, `TREND_ANALYSIS` | `deepseek-r1:8b` |

El routing se configura en `infrastructure/llm/router.py` y se puede modificar desde `.env`:
```env
LLM_EXTRACTION_MODEL=qwen3:14b
LLM_REASONING_MODEL=deepseek-r1:8b
```

---

## Verificación Rápida

```bash
# Verificar configuración
python -c "from config.settings import get_settings; s = get_settings(); print(s.ollama.base_url)"

# Verificar imports core
python -c "from core import BasePlatform, ContentItem, TaskType; print('core OK')"

# Verificar infrastructure
python -c "from infrastructure import OllamaClient, PlaywrightManager, FileStorage; print('infrastructure OK')"

# Verificar prompts
python -c "from prompts import PromptRegistry; r = PromptRegistry(); print(r.list_templates())"
```

---

## Roadmap

### Fase 1 — Infraestructura ✅
- Configuración centralizada (Pydantic Settings)
- Cliente Ollama async con retry y streaming
- LLM Router (selección de modelo por TaskType)
- Playwright Manager (Chromium, stealth config)
- Sistema de almacenamiento async (JSON + Markdown)
- Sistema de prompts versionado
- Jerarquía de excepciones typed
- Contratos base (ABCs)

### Fase 2 — YouTube Researcher 🔜
- Extractor de búsqueda de YouTube
- Extractor de metadata de video
- Extractor de información de canal
- Analizador de tendencias
- Detector de patrones (títulos, thumbnails, duración)

### Fases Futuras
- TikTok, Steam, Reddit, X, Twitch
- Análisis SEO y de sentimiento
- Comparador de canales
- Generador de reportes PDF
- Exportación estructurada

---

## Plataformas Hardware

| Componente | Especificación |
|---|---|
| GPU | RTX 5050 Laptop — 8 GB VRAM |
| RAM | 32 GB DDR5 |
| CPU | Intel Core i5 |
| OS | Windows 11 |

> **Nota VRAM:** `qwen3:14b` con Q4_K_M requiere ~8.5 GB. Con `OLLAMA_NUM_GPU_LAYERS=30`
> en tu `.env`, parte del modelo se descarga a RAM (offload parcial).
> Si experimentas errores de VRAM, reduce `OLLAMA_NUM_GPU_LAYERS` a 25.

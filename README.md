# 🚀 AI Content Research Framework — Analista de Videos Automático

> Framework modular e inteligente en Python para automatizar la investigación, análisis de tendencias y extracción de contenido digital en plataformas como YouTube, ejecutado **100% en local** con modelos LLM (Ollama) y Playwright.

---

## 📌 ¿De qué va el proyecto?

**Analista de Videos Automático** es un sistema diseñado para automatizar el análisis de contenido publicado en internet. Permite pasar de preguntas en lenguaje natural (ej. *"¿Qué patrones tienen los títulos exitosos de FNAF?"*, *"Analiza este canal"*, *"Encuentra oportunidades con poca competencia"*) a reportes estructurados con evidencia cuantitativa y cualitativa.

### ✨ Principales características

- 🔒 **100% Local & Privado:** Sin APIs comerciales ni costos por token. Todo procesado localmente con **Ollama** y **Playwright**.
- 🧠 **Orquestación Multi-Modelo (LLM Router):**
  - **Qwen3 14B:** Extracción, clasificación de títulos, patrones de clics y resúmenes estructurados.
  - **DeepSeek R1 8B:** Detección de patrones de mercado, razonamiento de competencia e identificación de nichos.
- 🧩 **Clean Architecture & SOLID:** Separación estricta entre contratos puros (`core/`), implementaciones (`infrastructure/`), y módulos por plataforma (`platforms/`).
- 🛠️ **CLI Interactivo:** Herramienta de línea de comandos rica desarrollada con **Typer** y **Rich**.

---

## 🏗️ Arquitectura del Sistema

```
AI-Content-Research/
├── core/                          # Contratos puros (ABCs) y modelos de datos
│   ├── interfaces/                # BasePlatform, BaseAnalyzer, BaseReporter
│   ├── models/                    # ContentItem, YouTubeVideo, LLMRequest, AnalysisResult
│   └── exceptions/                # Jerarquía tipada de excepciones del framework
│
├── infrastructure/                # Implementación concreta de servicios
│   ├── browser/                   # PlaywrightManager (Chromium stealth)
│   ├── llm/                       # OllamaClient (Async HTTP) & LLMRouter
│   ├── storage/                   # FileStorage (Persistencia JSON + Markdown)
│   └── logging/                   # Configuración centralizada de Loguru
│
├── platforms/                     # Módulos independientes por plataforma
│   ├── base/                      # PlatformBase con Inyección de Dependencias
│   └── youtube/                   # Extractores de búsqueda, video y canal
│
├── analysis/                      # Motores de análisis reutilizables
│   └── youtube/                   # TitleAnalyzer (Qwen3) & TrendAnalyzer (DeepSeek R1)
│
├── prompts/                       # Sistema de prompts versionados en Markdown
│   ├── registry.py                # Carga y caché LRU de templates
│   └── templates/                 # Archivos .md organizados por plataforma
│
├── cli/                           # CLI Interactivo (Typer + Rich)
│   └── main.py
│
└── tests/                         # Suite de pruebas unitarias
```

---

## 🚦 Requisitos Previos

1. **Python 3.11+**
2. **Ollama** corriendo en local (`http://localhost:11434`)
3. **Modelos Locales de Ollama:**
   ```bash
   ollama pull qwen3:14b
   ollama pull deepseek-r1:8b
   ```
4. **Hardware Recomendado:**
   - **GPU:** 8 GB VRAM (ej. RTX 4050/5050 Laptop o equivalente)
   - **RAM:** 16 GB - 32 GB DDR4/DDR5
   - **OS:** Windows 11 / Linux / macOS

---

## ⚡ Guía de Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/danielgalindo69/Analista-de-videos-automatico.git
cd Analista-de-videos-automatico/AI-Content-Research
```

### 2. Crear y activar entorno virtual
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Instalar navegador Chromium para Playwright
```bash
playwright install chromium
```

### 5. Configurar variables de entorno
```bash
copy .env.example .env     # Windows
cp .env.example .env       # Linux / macOS
```

---

## 🖥️ Uso de la CLI

Todos los comandos se ejecutan a través de `cli/main.py`:

### 1. Diagnóstico e Información del Sistema
Muestra los modelos configurados, URLs de Ollama y parámetros de almacenamiento:
```bash
python cli/main.py info
```

### 2. Búsqueda en YouTube en Tiempo Real
Scrapea y extrae metadatos de videos para cualquier consulta:
```bash
python cli/main.py search "Five Nights at Freddy's" --max 10
```

### 3. Análisis Inteligente Completo (Qwen3 + DeepSeek R1)
Extrae los videos y ejecuta ambos modelos LLM para generar reportes estructurados:
```bash
python cli/main.py analyze "Five Nights at Freddy's Fear's Mind" --max 10
```
> **Resultados:** Los reportes en `.json` y `.md` se guardan automáticamente en la carpeta `output/youtube/YYYY-MM-DD/analysis/`.

---

## 🤝 Guía para Colaboradores

¡Las contribuciones para expandir la plataforma son totalmente bienvenidas!

### Cómo agregar una nueva plataforma (ej. TikTok, Steam, Reddit):
1. Crea un módulo en `platforms/nombre_plataforma/`.
2. Hereda de `PlatformBase[TuModeloContentItem]` e implementa los métodos `search()`, `get_item()`, `get_trending()`.
3. Crea tus extractores DOM en `platforms/nombre_plataforma/extractors/`.
4. Define los templates de prompts correspondientes en `prompts/templates/nombre_plataforma/`.
5. Crea los analizadores específicos en `analysis/nombre_plataforma/`.

### Ejecutar Pruebas
```bash
python tests/test_youtube.py
```

---

## 📜 Licencia

MIT License — Código libre para uso, modificación y contribución comunitaria.

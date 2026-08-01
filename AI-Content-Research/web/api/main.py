"""
FastAPI backend for AI Content Research Framework.

Exposes REST endpoints to trigger YouTube search and LLM analysis,
with Server-Sent Events (SSE) for real-time progress updates to the UI.
"""

import asyncio
import sys
from pathlib import Path

# Project root on sys.path so we can import existing modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.api.routes import router

app = FastAPI(
    title="AI Content Research API",
    description="Backend for the AI Content Research Framework",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI Content Research API"}

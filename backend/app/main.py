"""Tax Mitra API — FastAPI service.

Serves the API under /api and, when the frontend has been built, the React
app from frontend/dist at the root — one service, one public link.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.ai.cache import get_store
from app.config import get_settings
from app.knowledge.retriever import Retriever
from app.routers import ai as ai_router
from app.routers import notices as notices_router
from app.routers import workflow as workflow_router
from app.routers.ai import limiter

app = FastAPI(
    title="Tax Mitra API",
    version="0.1.0",
    description="Your tax notice, made understandable. Independent prototype; all data is fictional.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notices_router.router)
app.include_router(workflow_router.router)
app.include_router(ai_router.router)


@app.get("/api/health")
def health():
    settings = get_settings()
    store = get_store()
    return {
        "status": "ok",
        "version": app.version,
        "demo_mode": settings.demo_mode,
        "live_ai_allowed": store.live_allowed(),
        "kb_loaded": Retriever.load(settings) is not None,
        "chat_model": settings.openai_chat_model,
    }


_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_INDEX = _FRONTEND_DIST / "index.html"

if _INDEX.exists():
    _assets = _FRONTEND_DIST / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_INDEX)

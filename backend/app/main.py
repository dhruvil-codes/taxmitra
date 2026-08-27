"""Tax Mitra API — FastAPI service.

Serves the API under /api and, when the frontend has been built, the React
app from frontend/dist at the root — one service, one public link.

Hardening on top of the routes themselves:
  * GZip responses (the low-bandwidth mobile story)
  * security headers on every response
  * one-line request logging (method, path, status, duration)
  * an enriched /api/health that doubles as a deployment dashboard and
    self-checks that every static fallback citation resolves in the corpus
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.ai.cache import get_store
from app.config import get_settings
from app.knowledge.corpus_loader import corpus_index
from app.knowledge.grounding import available_method
from app.knowledge.retriever import Retriever
from app.routers import ai as ai_router
from app.routers import notices as notices_router
from app.routers import scrutiny as scrutiny_router
from app.routers import workflow as workflow_router
from app.routers.ai import limiter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("taxmitra")

app = FastAPI(
    title="Tax Mitra API",
    version="0.2.0",
    description="Your tax notice, made understandable. Independent prototype; all data is fictional.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(GZipMiddleware, minimum_size=1024)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability_and_security_headers(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    logger.info("%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, duration_ms)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


app.include_router(notices_router.router)
app.include_router(workflow_router.router)
app.include_router(ai_router.router)
app.include_router(scrutiny_router.router)


def _static_integrity() -> dict:
    """Every citation id inside a static fallback must resolve to a corpus chunk.

    This is the class of bug we already caught once (a loader that dropped
    the id field silently emptied all citations); the check makes it impossible
    to ship quietly again.
    """
    settings = get_settings()
    index = corpus_index(os.path.join(str(settings.kb_dir), "corpus"))
    problems: list[str] = []
    for key, payload in get_store().static_items():
        for cid in payload.get("citations", ()):
            if cid not in index:
                problems.append(f"{key}: unresolved citation '{cid}'")
    return {"status": "ok" if not problems else "broken", "problems": problems}


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
        "embedding_model": settings.openai_embedding_model,
        "retrieval_method": available_method(settings),
        "static_fallbacks": len(store.static_items()),
        "static_integrity": _static_integrity()["status"],
    }


_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_INDEX = _FRONTEND_DIST / "index.html"

if _INDEX.exists():
    _assets = _FRONTEND_DIST / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        # Containment check: never serve files that resolve outside dist/.
        candidate = (_FRONTEND_DIST / full_path).resolve()
        dist_root = _FRONTEND_DIST.resolve()
        if full_path and candidate.is_file() and dist_root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(_INDEX)

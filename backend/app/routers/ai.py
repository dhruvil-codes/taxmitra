"""AI explanation endpoint — static-first, DEMO_MODE-aware, cited, grounded.

Serving chain (per request):
  1. in-memory cache   -> source: "cache"
  2. static fallback   -> source: "static"   (the designed path; DEMO_MODE stops here)
  3. live OpenAI call  -> source: "live"     (dev-time only; grounded + confidence-gated)

Every response carries `grounding` metadata (method + confidence + refusal
flag) so the frontend can always show how the answer was anchored, and
`degraded` is True only when we serve stale cache because live AI is off.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.ai.cache import get_store
from app.ai.prompts import build_explanation_prompt
from app.ai.provider import ChatProvider
from app.config import get_settings
from app.data_store import get_notice
import os

from app.knowledge.corpus_loader import citations_for
from app.knowledge.embedder import AIUnavailableError
from app.knowledge.grounding import ground
from app.knowledge.retriever import RetrievalResult
from app.rules.decision_trees import localized_income_source, render_text
from app.rules.notice_types import NoticeCategory, classify_notice, is_supported

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/ai", tags=["ai"])

_TEXT_FIELDS = ("plain_language", "what_this_does_not_mean")


def _render_fields(content: dict, notice: dict, locale: str) -> dict:
    rendered = dict(content)
    for field in _TEXT_FIELDS:
        if field in rendered:
            rendered[field] = render_text(str(rendered[field]), notice, locale)
    if isinstance(rendered.get("possible_reasons"), list):
        rendered["possible_reasons"] = [
            render_text(str(reason), notice, locale) for reason in rendered["possible_reasons"]
        ]
    return rendered


def _grounding_payload(result: RetrievalResult) -> dict:
    return {
        "method": result.method,
        "confidence": round(result.confidence, 3),
        "below_floor": result.below_floor,
        "verified_source_count": result.verified_source_count,
        "verified": result.verified_source_count > 0,
    }


def _http_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="AI explanation temporarily unavailable; please retry later.")


@router.get("/explanation/{notice_id}")
@limiter.limit(get_settings().ai_rate_limit)
def explanation(request: Request, notice_id: str, locale: str = Query(default="en", pattern="^(en|hi)$")):
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    category = classify_notice(notice)
    if category == NoticeCategory.SCRUTINY_142_1:
        raise HTTPException(status_code=400, detail="Use /api/scrutiny endpoints for 142(1) request-level explanations")
    if not is_supported(category):
        raise HTTPException(status_code=400, detail="Notice not supported; see refusal endpoint")

    settings = get_settings()
    store = get_store()
    key = f"explanation_{category.value}_{locale}"
    query = (
        f"explain {notice['section']} income mismatch intimation "
        f"{localized_income_source(notice, 'en')}"
    )

    content = store.get_memory(key)
    source = "cache" if content is not None else None
    if content is None:
        content = store.get_static(key)
        if content is not None:
            source = "static"

    grounding: RetrievalResult | None = None

    if content is None:
        # Dev-time generation: grounded in retrieved official-source context,
        # gated by the confidence floor. Never reached in DEMO_MODE.
        if not store.live_allowed():
            raise _http_unavailable()
        grounding = ground(settings, query)
        if grounding.below_floor or grounding.verified_source_count == 0:
            raise _http_unavailable()
        if not grounding.chunks:
            raise _http_unavailable()
        try:
            provider = ChatProvider(settings)
            system, user = build_explanation_prompt(notice, grounding.chunks, locale)
            content = provider.chat_json(system, user)
            store.put_memory(key, content)
            source = "live"
        except AIUnavailableError:
            raise _http_unavailable()

    if grounding is None:
        # Static/cache path: grounding is still computed (lexical, zero cost,
        # zero network) so every response reports how it is anchored.
        grounding = ground(settings, query)

    payload = _render_fields(content, notice, locale)
    citation_ids = tuple(payload.get("citations", ()))
    return {
        "content": {
            "plain_language": payload.get("plain_language", ""),
            "what_this_does_not_mean": payload.get("what_this_does_not_mean", ""),
            "possible_reasons": payload.get("possible_reasons", []),
        },
        "citations": citations_for(citation_ids, os.path.join(str(settings.kb_dir), "corpus")),
        "scope_statement": {
            "en": "Covers only the listed notice types. The official Income Tax portal remains authoritative.",
            "hi": "केवल सूचीबद्ध नोटिस प्रकारों को शामिल करता है। आधिकारिक आयकर पोर्टल ही प्रमाणिक स्रोत है।",
        },
        "source": source,
        "degraded": source == "cache" and not store.live_allowed(),
        "demo_mode": settings.demo_mode,
        "grounding": _grounding_payload(grounding),
    }

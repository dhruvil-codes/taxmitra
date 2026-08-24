"""AI explanation endpoint — static-first, DEMO_MODE-aware, cited."""

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
from app.knowledge.retriever import Retriever
from app.rules.decision_trees import render_text
from app.rules.notice_types import classify_notice, is_supported

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/ai", tags=["ai"])

_TEXT_FIELDS = ("plain_language", "what_this_does_not_mean")


def _render_fields(content: dict, notice: dict) -> dict:
    rendered = dict(content)
    for field in _TEXT_FIELDS:
        if field in rendered:
            rendered[field] = render_text(str(rendered[field]), notice)
    if isinstance(rendered.get("possible_reasons"), list):
        rendered["possible_reasons"] = [
            render_text(str(reason), notice) for reason in rendered["possible_reasons"]
        ]
    return rendered


@router.get("/explanation/{notice_id}")
@limiter.limit(get_settings().ai_rate_limit)
def explanation(request: Request, notice_id: str, locale: str = Query(default="en", pattern="^(en|hi)$")):
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    category = classify_notice(notice)
    if not is_supported(category):
        raise HTTPException(status_code=400, detail="Notice not supported; see refusal endpoint")

    settings = get_settings()
    store = get_store()
    key = f"explanation_{category.value}_{locale}"

    content = store.get_memory(key) or store.get_static(key)
    source = "static" if store.get_static(key) is not None else "cache"
    degraded = False

    if content is None:
        if not store.live_allowed():
            raise HTTPUnavailable()
        # Dev-time generation: grounded in retrieved official-source context.
        retriever = Retriever.load(settings)
        if retriever is None:
            raise HTTPUnavailable()
        try:
            provider = ChatProvider(settings)
            query = f"explain {notice['section']} income mismatch intimation {notice['income_source']}"
            from app.knowledge.embedder import Embedder

            vector = Embedder(settings).embed_texts([query])[0]
            result = retriever.retrieve(vector)
            if result.below_floor:
                raise HTTPUnavailable()
            system, user = build_explanation_prompt(notice, result.chunks, locale)
            content = provider.chat_json(system, user)
            store.put_memory(key, content)
            source = "live"
        except AIUnavailableError as exc:
            raise HTTPUnavailable() from exc

    payload = _render_fields(content, notice)
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
        "degraded": degraded,
        "demo_mode": settings.demo_mode,
    }


def HTTPUnavailable():  # small helper for consistent 503s
    return HTTPException(status_code=503, detail="AI explanation temporarily unavailable; please retry later.")

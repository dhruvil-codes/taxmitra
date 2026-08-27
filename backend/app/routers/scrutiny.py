"""Section 142(1) scrutiny workflow endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings
from app.data_store import get_notice
from app.knowledge.corpus_loader import citations_for
from app.knowledge.grounding import ground
from app.rules.notice_types import NoticeCategory, classify_notice
from app.rules.scrutiny import (
    build_scrutiny_requests,
    insufficient_information_refusal,
    questions_payload,
    request_payload,
    resolve_scrutiny,
    scrutiny_questions,
)

router = APIRouter(prefix="/api/scrutiny", tags=["scrutiny"])


class ScrutinyResolveRequest(BaseModel):
    notice_id: str
    answers: dict[str, str]
    extraction_confirmed: bool = True


def _scrutiny_notice(notice_id: str) -> dict:
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    if classify_notice(notice) != NoticeCategory.SCRUTINY_142_1:
        raise HTTPException(status_code=400, detail="Notice is not a supported 142(1) scrutiny notice")
    return notice


def _citations_by_request(requests) -> dict[str, list[dict]]:
    settings = get_settings()
    corpus_dir = os.path.join(str(settings.kb_dir), "corpus")
    return {
        request.id: citations_for(request.citations, corpus_dir)
        for request in requests
    }


def _grounding_payload(notice: dict) -> dict:
    settings = get_settings()
    query = f"explain section 142(1) scrutiny notice accounts documents information {notice.get('assessment_year', '')}"
    result = ground(settings, query)
    return {
        "method": result.method,
        "confidence": round(result.confidence, 3),
        "below_floor": result.below_floor,
    }


@router.get("/{notice_id}/requests")
def requests(
    notice_id: str,
    locale: str = Query(default="en", pattern="^(en|hi)$"),
    extraction_confirmed: bool = Query(default=True),
):
    notice = _scrutiny_notice(notice_id)
    found = build_scrutiny_requests(notice, extraction_confirmed=extraction_confirmed)
    if not found:
        return insufficient_information_refusal("Extraction has not been confirmed or no annexure requests were found.")
    return {
        "supported": True,
        "notice_id": notice_id,
        "locale": locale,
        "extraction": {
            "source_type": (notice.get("synthetic_extraction") or {}).get("source_type", "unknown"),
            "requires_human_confirmation": bool((notice.get("synthetic_extraction") or {}).get("requires_human_confirmation", True)),
            "confirmed": extraction_confirmed,
        },
        "requests": request_payload(found, _citations_by_request(found)),
        "grounding": _grounding_payload(notice),
    }


@router.get("/{notice_id}/questions")
def questions(
    notice_id: str,
    locale: str = Query(default="en", pattern="^(en|hi)$"),
    extraction_confirmed: bool = Query(default=True),
):
    notice = _scrutiny_notice(notice_id)
    found = build_scrutiny_requests(notice, extraction_confirmed=extraction_confirmed)
    if not found:
        return insufficient_information_refusal("Extraction has not been confirmed or no annexure requests were found.")
    return {
        "supported": True,
        "notice_id": notice_id,
        "questions": questions_payload(scrutiny_questions(found), locale),
    }


@router.post("/resolve")
def resolve(payload: ScrutinyResolveRequest):
    notice = _scrutiny_notice(payload.notice_id)
    try:
        return resolve_scrutiny(
            notice,
            payload.answers,
            extraction_confirmed=payload.extraction_confirmed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

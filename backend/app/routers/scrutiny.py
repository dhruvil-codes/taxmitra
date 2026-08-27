"""Section 142(1) scrutiny workflow endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
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
from app.extraction.pdf import MAX_PDF_BYTES, extract_pdf
from app.extraction.sessions import confirm_session, create_session, get_session

router = APIRouter(prefix="/api/scrutiny", tags=["scrutiny"])


class ScrutinyResolveRequest(BaseModel):
    notice_id: str
    answers: dict[str, str]
    extraction_confirmed: bool = True


class ExtractionConfirmation(BaseModel):
    extraction_id: str
    fingerprint: str
    confirmed: bool


def _session_notice(extraction_id: str) -> dict | None:
    session = get_session(extraction_id)
    if not session or not session.get("confirmed"):
        return None
    metadata = session["metadata"]
    return {
        "id": extraction_id,
        "section": metadata["section"],
        "assessment_year": metadata.get("assessment_year"),
        "response_due_date": metadata.get("response_deadline"),
        "issue_date": metadata.get("issue_date"),
        "official_reference": metadata.get("notice_reference"),
        "synthetic_extraction": {"source_type": "pdf", "requires_human_confirmation": True, "requests": session["requests"]},
    }


def _scrutiny_notice(notice_id: str) -> dict:
    notice = get_notice(notice_id)
    if notice is None:
        session = get_session(notice_id)
        if session is not None and not session.get("confirmed"):
            raise HTTPException(status_code=409, detail="Human confirmation is required before scrutiny guidance")
        notice = _session_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    if classify_notice(notice) != NoticeCategory.SCRUTINY_142_1:
        raise HTTPException(status_code=400, detail="Notice is not a supported 142(1) scrutiny notice")
    return notice


@router.post("/extract")
async def extract(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only application/pdf is accepted")
    content = await file.read(MAX_PDF_BYTES + 1)
    settings = get_settings()
    result = extract_pdf(content, lambda query: ground(settings, query))
    preview_notice = {
        "section": result.metadata.get("section"),
        "synthetic_extraction": {"source_type": "pdf", "requires_human_confirmation": True, "requests": list(result.requests)},
    }
    enriched = build_scrutiny_requests(preview_notice, True) if not result.refusal_reason else ()
    payload = {
        "metadata": result.metadata,
        "requests": request_payload(enriched, _citations_by_request(enriched)),
        "extraction": {
            "status": "refused" if result.refusal_reason else "needs_confirmation",
            "confidence": result.extraction_confidence,
            "warnings": list(result.warnings),
            "refusal_reason": result.refusal_reason,
        },
        "grounding": {"method": result.grounding_method, "confidence": result.grounding_confidence, "below_floor": result.grounding_below_floor},
    }
    if result.refusal_reason:
        return {**payload, "supported": False}
    extraction_id, fingerprint = create_session(payload)
    return {**payload, "supported": True, "extraction_id": extraction_id, "fingerprint": fingerprint, "requires_human_confirmation": True}


@router.post("/confirm")
def confirm(payload: ExtractionConfirmation):
    if not payload.confirmed:
        return {"supported": False, "status": "refused", "reason": "Human confirmation was not provided."}
    session = confirm_session(payload.extraction_id, payload.fingerprint)
    if session is None:
        raise HTTPException(status_code=409, detail="Extraction session or fingerprint is invalid or expired")
    notice = _session_notice(payload.extraction_id)
    return {"supported": True, "status": "confirmed", "extraction_id": payload.extraction_id, "notice_id": payload.extraction_id, "requests": request_payload(build_scrutiny_requests(notice, True), _citations_by_request(build_scrutiny_requests(notice, True)))}


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

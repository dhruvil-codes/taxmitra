"""Section 142(1) scrutiny workflow endpoints."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from app.config import get_settings
from app.data_store import get_notice
from app.knowledge.corpus_loader import citations_for
from app.knowledge.grounding import ground
from app.rules.notice_types import NoticeCategory, classify_notice
from app.rules.scrutiny import (
    build_scrutiny_requests,
    insufficient_information_refusal,
    minimum_question_plan,
    minimum_question_plan_payload,
    questions_payload,
    request_payload,
    resolve_scrutiny,
    scrutiny_questions,
)
from app.extraction.pdf import MAX_PDF_BYTES, extract_pdf
from app.extraction.sessions import confirm_session, create_session, get_session
from app.evidence.mapping import DOCUMENT_STATUSES, map_evidence, missing_evidence
from app.review.safety import evaluate

router = APIRouter(prefix="/api/scrutiny", tags=["scrutiny"])


class ScrutinyResolveRequest(BaseModel):
    notice_id: str
    answers: dict[str, str]
    extraction_confirmed: bool = True
    document_statuses: dict[str, str] = {}


class EvidenceStatusUpdate(BaseModel):
    statuses: dict[str, str] = {}


class ScrutinyReviewRequest(BaseModel):
    answers: dict[str, str]
    document_statuses: dict[str, str] = {}
    draft: str
    approved: bool = False
    extraction_confirmed: bool = True


class ExtractionConfirmation(BaseModel):
    extraction_id: str
    fingerprint: str
    confirmed: bool
    corrections: dict[str, str] = {}


class QuestionPlanRequest(BaseModel):
    notice_id: str
    answers: dict[str, str] = {}
    extraction_confirmed: bool = True


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
    logger.info(f"PDF EXTRACTION START: filename={file.filename}, content_type={file.content_type}")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only application/pdf is accepted")
    content = await file.read(MAX_PDF_BYTES + 1)
    logger.info(f"PDF BYTES RECEIVED: size={len(content)} bytes, file_successfully_read={len(content) > 0}")
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
            "status": result.status if not result.refusal_reason else "refused",
            "confidence": result.extraction_confidence,
            "warnings": list(result.warnings),
            "refusal_reason": result.refusal_reason,
            "error_code": result.error_code,
            "method": result.extraction_method,
            "page_count": result.page_count,
        },
        "grounding": {"method": result.grounding_method, "confidence": result.grounding_confidence, "below_floor": result.grounding_below_floor},
        "document": {"status": "extracted" if not result.refusal_reason else "uploaded", "page_count": result.page_count, "sha256": result.original_pdf_sha256, "pages": list(result.pages)},
        "states": ["uploaded", "extracted" if result.pages else "uploaded", "needs_confirmation" if not result.refusal_reason else ("unsupported" if result.refusal_reason == "unsupported_notice" else "needs_confirmation"), "supported" if not result.refusal_reason else "unsupported"],
    }
    if result.refusal_reason:
        return {**payload, "supported": False}
    extraction_id, fingerprint = create_session(payload, content)
    return {**payload, "supported": True, "extraction_id": extraction_id, "fingerprint": fingerprint, "requires_human_confirmation": True}


@router.post("/confirm")
def confirm(payload: ExtractionConfirmation):
    if not payload.confirmed:
        return {"supported": False, "status": "refused", "reason": "Human confirmation was not provided."}
    session = confirm_session(payload.extraction_id, payload.fingerprint, payload.corrections)
    if session is None:
        raise HTTPException(status_code=409, detail="Extraction session or fingerprint is invalid or expired")
    notice = _session_notice(payload.extraction_id)
    return {"supported": True, "status": "confirmed", "states": ["uploaded", "extracted", "needs_confirmation", "confirmed", "supported"], "extraction_id": payload.extraction_id, "notice_id": payload.extraction_id, "requests": request_payload(build_scrutiny_requests(notice, True), _citations_by_request(build_scrutiny_requests(notice, True)))}


def _citations_by_request(requests) -> dict[str, list[dict]]:
    settings = get_settings()
    corpus_dir = os.path.join(str(settings.kb_dir), "corpus")
    return {
        request.id: citations_for(request.citations, corpus_dir)
        for request in requests
    }


def _sources_verified(requests) -> bool:
    """Rules and draft generation may proceed only with current official sources."""
    citations = _citations_by_request(requests)
    return bool(requests) and all(
        any(c.get("verification_status") == "VERIFIED_OFFICIAL" and c.get("status") == "CURRENT" for c in citations.get(request.id, []))
        for request in requests
    )


def _evidence_for_notice(notice: dict, statuses: dict[str, str] | None = None) -> list[dict]:
    found = build_scrutiny_requests(notice, extraction_confirmed=True)
    return map_evidence(found, statuses)


def _grounding_payload(notice: dict) -> dict:
    settings = get_settings()
    query = f"explain section 142(1) scrutiny notice accounts documents information {notice.get('assessment_year', '')}"
    result = ground(settings, query)
    return {
        "method": result.method,
        "confidence": round(result.confidence, 3),
        "below_floor": result.below_floor,
        "verified_source_count": result.verified_source_count,
        "verified": result.verified_source_count > 0,
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
    if not _sources_verified(found):
        return insufficient_information_refusal("At least one request has no current verified official source, so Tax Mitra cannot safely explain it.")
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
        "evidence": _evidence_for_notice(notice),
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
    if not _sources_verified(found):
        return insufficient_information_refusal("At least one request has no current verified official source, so Tax Mitra cannot safely ask for evidence.")
    return {
        "supported": True,
        "notice_id": notice_id,
        "questions": questions_payload(scrutiny_questions(found), locale),
    }


@router.get("/{notice_id}/question-plan")
def question_plan(
    notice_id: str,
    locale: str = Query(default="en", pattern="^(en|hi)$"),
    extraction_confirmed: bool = Query(default=True),
):
    """Return only questions whose answers can change the safe next step.

    The original ``/questions`` endpoint remains unchanged for existing
    clients. New clients should use this endpoint for the simplified flow.
    """
    notice = _scrutiny_notice(notice_id)
    found = build_scrutiny_requests(notice, extraction_confirmed=extraction_confirmed)
    if not found:
        return insufficient_information_refusal("Extraction has not been confirmed or no annexure requests were found.")
    if not _sources_verified(found):
        return insufficient_information_refusal("At least one request has no current verified official source, so Tax Mitra cannot safely ask for evidence.")
    plan = minimum_question_plan(found)
    return {
        "supported": True,
        "notice_id": notice_id,
        "locale": locale,
        "request_count": len(found),
        "question_count": len(plan),
        "questions": minimum_question_plan_payload(plan, locale),
        "evidence": _evidence_for_notice(notice),
        "grounding": _grounding_payload(notice),
    }


@router.post("/question-plan")
def next_question_plan(payload: QuestionPlanRequest):
    """Return conditional follow-ups after answers to the minimum plan."""
    notice = _scrutiny_notice(payload.notice_id)
    found = build_scrutiny_requests(notice, extraction_confirmed=payload.extraction_confirmed)
    if not found:
        return insufficient_information_refusal("Extraction has not been confirmed or no annexure requests were found.")
    if not _sources_verified(found):
        return insufficient_information_refusal("At least one request has no current verified official source, so Tax Mitra cannot safely ask for evidence.")
    plan = minimum_question_plan(found, payload.answers)
    return {
        "supported": True,
        "notice_id": payload.notice_id,
        "request_count": len(found),
        "question_count": len(plan),
        "questions": minimum_question_plan_payload(plan, "en"),
    }


@router.post("/resolve")
def resolve(payload: ScrutinyResolveRequest):
    notice = _scrutiny_notice(payload.notice_id)
    if not _sources_verified(build_scrutiny_requests(notice, extraction_confirmed=payload.extraction_confirmed)):
        return insufficient_information_refusal("The request sources are not verified enough to prepare a safe response path.")
    try:
        response = resolve_scrutiny(
            notice,
            payload.answers,
            extraction_confirmed=payload.extraction_confirmed,
        )
        evidence = _evidence_for_notice(notice, payload.document_statuses)
        review = evaluate(notice, build_scrutiny_requests(notice, payload.extraction_confirmed), payload.answers, evidence, response.get("draft", ""), supported=True, extraction_confirmed=payload.extraction_confirmed, verified_sources=True)
        return {**response, "evidence": evidence, "missing_evidence": missing_evidence(evidence), "safety_review": review}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{notice_id}/evidence")
def update_evidence_status(notice_id: str, payload: EvidenceStatusUpdate):
    """Validate and project local document statuses; no taxpayer files are stored."""
    notice = _scrutiny_notice(notice_id)
    invalid = {key: value for key, value in payload.statuses.items() if value not in DOCUMENT_STATUSES}
    if invalid:
        raise HTTPException(status_code=422, detail=f"Invalid document status for: {', '.join(sorted(invalid))}")
    evidence = _evidence_for_notice(notice, payload.statuses)
    return {"notice_id": notice_id, "evidence": evidence, "missing_evidence": missing_evidence(evidence), "storage": "local_or_browser_only"}


@router.post("/{notice_id}/review")
def approve_review(notice_id: str, payload: ScrutinyReviewRequest):
    """Final approval gate. It never submits or uploads anything."""
    notice = _scrutiny_notice(notice_id)
    found = build_scrutiny_requests(notice, payload.extraction_confirmed)
    if not _sources_verified(found):
        return {"status": "blocked", "handoff_allowed": False, "message": "Tax Mitra can't safely prepare this yet.", "missing": ["Important explanations are not grounded in verified sources."]}
    try:
        resolved = resolve_scrutiny(notice, payload.answers, payload.extraction_confirmed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    evidence = _evidence_for_notice(notice, payload.document_statuses)
    safety = evaluate(notice, found, payload.answers, evidence, payload.draft, supported=True, extraction_confirmed=payload.extraction_confirmed, verified_sources=True)
    if not payload.approved or not safety["ready"]:
        return {"status": "blocked", "handoff_allowed": False, "message": "Tax Mitra can't safely prepare this yet.", "missing": safety["missing"], "safety_review": safety, "missing_evidence": missing_evidence(evidence)}
    return {"status": "approved", "handoff_allowed": True, "safety_review": safety, "official_step": resolved["official_step"], "message": "Your response is ready to review on the official Income Tax e-Filing portal.", "boundary": "Tax Mitra does not submit anything to the government."}

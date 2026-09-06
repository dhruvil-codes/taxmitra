"""Workflow endpoints: guided questions and deterministic path resolution."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.data_store import get_citizen, get_notice, load_draft_templates
from app.rules.decision_trees import get_questions, valid_answer
from app.rules.response_paths import questions_payload
from app.rules.notice_types import NoticeCategory, classify_notice, is_supported
from app.rules.refusal import build_refusal
from app.rules.response_paths import build_draft, resolve_path
from app.rules.checklists import checklist_for
from app.rules.deadlines import compute_due_date, days_remaining, deadline_status
from datetime import date
from app.extraction.sessions import get_session
from app.workflows.handlers import get_workflow_handler
from app.workflows.registry import WorkflowCapability, classify_extracted_notice, get_workflow

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class Answers(BaseModel):
    notice_id: str
    answers: dict[str, str]


def _notice_for_workflow(notice_id: str) -> dict:
    notice = get_notice(notice_id)
    if notice is not None:
        return notice
    session = get_session(notice_id)
    if session is None or not session.get("confirmed"):
        raise HTTPException(status_code=404, detail="Notice not found")
    metadata = session.get("metadata", {})
    return {
        "id": notice_id,
        "section": metadata.get("section"),
        "assessment_year": metadata.get("assessment_year"),
        "response_due_date": metadata.get("response_deadline"),
        "issue_date": metadata.get("issue_date"),
        "official_reference": metadata.get("notice_reference"),
        "citizen_id": "uploaded",
        "official_text": "\n".join(page.get("text", "") for page in session.get("pages", [])),
        "synthetic_extraction": {"source_type": "pdf", "requires_human_confirmation": True, "requests": session.get("requests", [])},
    }


@router.get("/questions/{notice_id}")
def questions(
    notice_id: str,
    locale: str = Query(default="en", pattern="^(en|hi)$"),
):
    notice = _notice_for_workflow(notice_id)
    classification = classify_extracted_notice(notice)
    category = NoticeCategory(classification.category) if classification.category in {item.value for item in NoticeCategory} else NoticeCategory.UNSUPPORTED
    if category == NoticeCategory.SCRUTINY_142_1:
        raise HTTPException(status_code=400, detail="Use /api/scrutiny endpoints for 142(1) scrutiny notices")
    definition = get_workflow(classification.category)
    if not definition or definition.capability in {WorkflowCapability.SAFE_STOP, WorkflowCapability.EXPLANATION_ONLY}:
        raise HTTPException(status_code=400, detail="Notice not supported")
    handler = get_workflow_handler(classification.category)
    return handler.get_questions(notice, locale)


@router.post("/resolve")
def resolve(payload: Answers):
    notice = _notice_for_workflow(payload.notice_id)
    classification = classify_extracted_notice(notice)
    category = NoticeCategory(classification.category) if classification.category in {item.value for item in NoticeCategory} else NoticeCategory.UNSUPPORTED
    if category == NoticeCategory.SCRUTINY_142_1:
        raise HTTPException(status_code=400, detail="Use /api/scrutiny/resolve for 142(1) scrutiny notices")
    definition = get_workflow(classification.category)
    if not definition or definition.capability in {WorkflowCapability.SAFE_STOP, WorkflowCapability.EXPLANATION_ONLY}:
        return {**build_refusal(category), "classification": classification.payload(), "workflow": definition.payload() if definition else None}

    try:
        result = get_workflow_handler(classification.category).resolve(notice, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not result.get("supported"):
        return result
    return {
        **result,
        "official_step": {
            "label": {"en": "Submit your response on the official e-Filing portal", "hi": "आधिकारिक e-Filing पोर्टल पर अपना उत्तर जमा करें"},
            "url": "https://www.incometax.gov.in/iec/foservices/",
            "boundary": {
                "en": "Tax Mitra has not submitted your response. Nothing has been sent to the Income Tax Department.",
                "hi": "Tax Mitra ने आपका उत्तर जमा नहीं किया है। आयकर विभाग को कुछ भी नहीं भेजा गया है।",
            },
        },
    }

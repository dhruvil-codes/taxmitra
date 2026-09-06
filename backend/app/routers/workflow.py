"""Workflow endpoints: guided questions and deterministic path resolution."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, field_validator

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
from app.workflows.handlers import get_workflow_handler, grounding_payload
from app.workflows.registry import WorkflowCapability, classify_extracted_notice, get_workflow
from app.workflows.official import official_portal_payload

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class Answers(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notice_id: str
    answers: dict[str, str | list[str] | dict[str, str] | int | float]

    @field_validator("answers")
    @classmethod
    def validate_answer_values(cls, values):
        for key, value in values.items():
            if isinstance(value, dict):
                if set(value) - {"choice", "other"} or not isinstance(value.get("choice"), str):
                    raise ValueError(f"Invalid choice-with-other answer for {key}")
                if "other" in value and not isinstance(value["other"], str):
                    raise ValueError(f"Invalid other answer for {key}")
            elif isinstance(value, list):
                if not all(isinstance(item, str) for item in value):
                    raise ValueError(f"Invalid multi-choice answer for {key}")
            elif not isinstance(value, (str, int, float)):
                raise ValueError(f"Invalid answer for {key}")
        return values


def _question_type(question: dict) -> str:
    return str(question.get("question_type") or question.get("type") or "text")


def _active(question: dict, answers: dict) -> bool:
    for condition in question.get("conditions") or []:
        if answers.get(condition.get("depends_on")) != condition.get("equals"):
            return False
    return True


def _validate_against_questions(questions: list[dict], answers: dict) -> None:
    by_id = {str(q.get("id") or q.get("question_id")): q for q in questions}
    for question_id, question in by_id.items():
        if not _active(question, answers):
            continue
        value = answers.get(question_id)
        if value is None or value == "" or value == []:
            if question.get("required", True):
                raise HTTPException(status_code=422, detail=f"Missing answer for question {question_id}")
            continue
        kind = _question_type(question)
        options = {str(option.get("id")) for option in question.get("options") or []}
        values = value if isinstance(value, list) else [value.get("choice")] if isinstance(value, dict) else [value]
        if kind in {"single_choice", "yes_no", "choice_with_other"}:
            if not all(isinstance(item, str) and item in options for item in values):
                raise HTTPException(status_code=422, detail=f"Invalid option for question {question_id}")
            if kind == "choice_with_other" and values[0] in {"other", "something_else"} and not str(value.get("other", "")).strip():
                raise HTTPException(status_code=422, detail=f"Please describe the other answer for {question_id}")
        elif kind == "multi_choice":
            if not isinstance(value, list) or not all(isinstance(item, str) and item in options for item in value):
                raise HTTPException(status_code=422, detail=f"Invalid multi-choice answer for question {question_id}")
        elif kind == "number" and not isinstance(value, (int, float, str)):
            raise HTTPException(status_code=422, detail=f"Invalid number for question {question_id}")
        elif kind == "date" and not isinstance(value, str):
            raise HTTPException(status_code=422, detail=f"Invalid date for question {question_id}")


def _notice_for_workflow(notice_id: str) -> dict:
    notice = get_notice(notice_id)
    if notice is not None:
        return notice
    session = get_session(notice_id)
    if session is None or not session.get("confirmed"):
        raise HTTPException(status_code=404, detail="Notice not found")
    metadata = session.get("metadata", {})
    stored = dict(session.get("notice") or {})
    return {
        **stored,
        "id": notice_id,
        "section": metadata.get("section"),
        "assessment_year": metadata.get("assessment_year"),
        "response_due_date": metadata.get("response_deadline"),
        "issue_date": metadata.get("issue_date"),
        "official_reference": metadata.get("notice_reference"),
        "citizen_id": "uploaded",
        "official_text": "\n".join(page.get("text", "") for page in session.get("pages", [])),
        "synthetic_extraction": {**(stored.get("synthetic_extraction") or {}), "source_type": "pdf", "requires_human_confirmation": True, "requests": session.get("requests", [])},
    }


@router.get("/questions/{notice_id}")
def questions(
    notice_id: str,
    locale: str = Query(default="en", pattern="^(en|hi)$"),
):
    notice = _notice_for_workflow(notice_id)
    classification = classify_extracted_notice(notice)
    category = NoticeCategory(classification.category) if classification.category in {item.value for item in NoticeCategory} else NoticeCategory.UNSUPPORTED
    definition = get_workflow(classification.category)
    if not definition or definition.capability in {WorkflowCapability.SAFE_STOP, WorkflowCapability.EXPLANATION_ONLY}:
        raise HTTPException(status_code=400, detail="Notice not supported")
    handler = get_workflow_handler(classification.category)
    response = handler.get_questions(notice, locale)
    response["grounding"] = grounding_payload(notice, classification.category)
    return response


@router.post("/resolve")
def resolve(payload: Answers):
    notice = _notice_for_workflow(payload.notice_id)
    classification = classify_extracted_notice(notice)
    category = NoticeCategory(classification.category) if classification.category in {item.value for item in NoticeCategory} else NoticeCategory.UNSUPPORTED
    definition = get_workflow(classification.category)
    if not definition or definition.capability in {WorkflowCapability.SAFE_STOP, WorkflowCapability.EXPLANATION_ONLY}:
        return {**build_refusal(category), "classification": classification.payload(), "workflow": definition.payload() if definition else None}

    try:
        question_payload = get_workflow_handler(classification.category).get_questions(notice, "en", payload.answers)
        _validate_against_questions(question_payload.get("questions", []), payload.answers)
        result = get_workflow_handler(classification.category).resolve(notice, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not result.get("supported"):
        return result
    return {
        **result,
        "grounding": result.get("grounding") or grounding_payload(notice, classification.category),
        "official_step": {
            "label": {"en": "Submit your response on the official e-Filing portal", "hi": "आधिकारिक e-Filing पोर्टल पर अपना उत्तर जमा करें"},
            "url": official_portal_payload()["url"],
            "boundary": {
                "en": "Tax Mitra has not submitted your response. Nothing has been sent to the Income Tax Department.",
                "hi": "Tax Mitra ने आपका उत्तर जमा नहीं किया है। आयकर विभाग को कुछ भी नहीं भेजा गया है।",
            },
        },
    }

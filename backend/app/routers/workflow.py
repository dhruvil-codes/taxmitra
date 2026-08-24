"""Workflow endpoints: guided questions and deterministic path resolution."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.data_store import get_citizen, get_notice, load_draft_templates
from app.rules.decision_trees import get_questions, valid_answer
from app.rules.response_paths import questions_payload
from app.rules.notice_types import classify_notice, is_supported
from app.rules.refusal import build_refusal
from app.rules.response_paths import build_draft, resolve_path
from app.rules.checklists import checklist_for
from app.rules.deadlines import compute_due_date, days_remaining, deadline_status
from datetime import date

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class Answers(BaseModel):
    notice_id: str
    answers: dict[str, str]


@router.get("/questions/{notice_id}")
def questions(notice_id: str, locale: str = "en"):
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    category = classify_notice(notice)
    if not is_supported(category):
        raise HTTPException(status_code=400, detail="Notice not supported")
    return {"questions": questions_payload(get_questions(category.value), notice, locale)}


@router.post("/resolve")
def resolve(payload: Answers):
    notice = get_notice(payload.notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    category = classify_notice(notice)
    if not is_supported(category):
        return build_refusal(category)

    questions = get_questions(category.value)
    expected = {q.id for q in questions}
    answers = payload.answers
    if not expected.issubset(answers.keys()):
        raise HTTPException(status_code=422, detail=f"Missing answers for: {sorted(expected - answers.keys())}")
    for key, value in answers.items():
        if key in expected and not valid_answer(value):
            raise HTTPException(status_code=422, detail=f"Invalid answer '{value}' for {key}")

    path = resolve_path(category, answers)
    if path is None:  # defensive — resolve_path is total for supported categories
        return build_refusal(category)

    issue_date = date.fromisoformat(notice["issue_date"])
    due = compute_due_date(issue_date, category)
    templates = load_draft_templates()
    template = templates[path.draft_template_id]
    draft = build_draft(template, notice, get_citizen(notice["citizen_id"]) or {}, answers, due)

    return {
        "supported": True,
        "path": {
            "path_id": path.path_id,
            "position": path.position,
            "headline": path.headline,
            "guidance": path.guidance,
        },
        "checklist": [
            {"id": item.id, "title": item.title, "why_needed": item.why_needed}
            for item in checklist_for(path.checklist_ids)
        ],
        "deadline": {
            "due_date": due.isoformat() if due else None,
            "days_remaining": days_remaining(due),
            "status": deadline_status(due),
        },
        "draft": draft,
        "official_step": {
            "label": {"en": "Submit your response on the official e-Filing portal", "hi": "आधिकारिक e-Filing पोर्टल पर अपना उत्तर जमा करें"},
            "url": "https://www.incometax.gov.in/iec/foservices/",
            "boundary": {
                "en": "Tax Mitra has not submitted your response. Nothing has been sent to the Income Tax Department.",
                "hi": "Tax Mitra ने आपका उत्तर जमा नहीं किया है। आयकर विभाग को कुछ भी नहीं भेजा गया है।",
            },
        },
    }

"""Common workflow handler boundary for supported and safe-stop workflows.

Handlers deliberately delegate to the existing deterministic rule modules. This
gives the API one extension point without duplicating or weakening those rules.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WorkflowHandler(ABC):
    category: str

    @abstractmethod
    def get_questions(self, notice: dict[str, Any], locale: str = "en", answers: dict[str, Any] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def resolve(self, notice: dict[str, Any], answers: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def get_evidence(self, notice: dict[str, Any], statuses: dict[str, str] | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def generate_response(self, notice: dict[str, Any], answers: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def review(self, notice: dict[str, Any], answers: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...


class Scrutiny142Handler(WorkflowHandler):
    category = "scrutiny_142_1"

    def _requests(self, notice: dict[str, Any], confirmed: bool = True):
        from app.rules.scrutiny import build_scrutiny_requests
        return build_scrutiny_requests(notice, confirmed)

    def get_questions(self, notice, locale="en", answers=None):
        from app.rules.scrutiny import minimum_question_plan, minimum_question_plan_payload
        plan = minimum_question_plan(self._requests(notice), answers)
        return {"questions": minimum_question_plan_payload(plan, locale)}

    def resolve(self, notice, answers, **kwargs):
        from app.rules.scrutiny import resolve_minimum_scrutiny
        return resolve_minimum_scrutiny(notice, answers, kwargs.get("document_statuses", {}), kwargs.get("extraction_confirmed", True))

    def get_evidence(self, notice, statuses=None):
        from app.evidence.mapping import map_evidence
        return map_evidence(self._requests(notice), statuses)

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)


class IncomeMismatch143Handler(WorkflowHandler):
    category = "income_mismatch_143_1a"

    def get_questions(self, notice, locale="en", answers=None):
        from app.rules.decision_trees import get_questions
        from app.rules.response_paths import questions_payload
        return {"questions": questions_payload(get_questions(self.category), notice, locale)}

    def resolve(self, notice, answers, **kwargs):
        from app.rules.decision_trees import get_questions, valid_answer
        from app.rules.response_paths import resolve_path, build_draft
        from app.rules.checklists import checklist_for
        from app.rules.deadlines import compute_due_date, days_remaining, deadline_status
        from app.data_store import get_citizen, load_draft_templates
        from datetime import date
        expected = {question.id for question in get_questions(self.category)}
        if not expected.issubset(answers):
            raise ValueError(f"Missing answers for: {sorted(expected - set(answers))}")
        if any(key in expected and not valid_answer(value) for key, value in answers.items()):
            raise ValueError("Invalid answer")
        path = resolve_path(self.category, answers)
        if path is None:
            return {"supported": False, "status": "safe_stop"}
        due = compute_due_date(date.fromisoformat(notice["issue_date"]), self.category)
        template = load_draft_templates()[path.draft_template_id]
        draft = build_draft(template, notice, get_citizen(notice["citizen_id"]) or {}, answers, due)
        return {"supported": True, "path": {"path_id": path.path_id, "position": path.position, "headline": path.headline, "guidance": path.guidance}, "checklist": [{"id": item.id, "title": item.title, "why_needed": item.why_needed} for item in checklist_for(path.checklist_ids)], "deadline": {"due_date": due.isoformat() if due else None, "days_remaining": days_remaining(due), "status": deadline_status(due)}, "draft": draft}

    def get_evidence(self, notice, statuses=None):
        from app.rules.checklists import checklist_for
        return [{"id": item.id, "title": item.title, "why_needed": item.why_needed} for item in checklist_for(())]

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        approved = bool(kwargs.get("approved", False))
        return {"status": "approved" if approved else "blocked", "handoff_allowed": approved, "message": "Official handoff remains blocked until explicit human approval." if not approved else "Response is ready for the taxpayer's official portal review."}


class SafeStopHandler(WorkflowHandler):
    category = "safe_stop"
    def _stop(self):
        return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "message": "This workflow is not implemented safely yet."}
    def get_questions(self, notice, locale="en", answers=None): return {"questions": [], **self._stop()}
    def resolve(self, notice, answers, **kwargs): return self._stop()
    def get_evidence(self, notice, statuses=None): return []
    def generate_response(self, notice, answers, **kwargs): return self._stop()
    def review(self, notice, answers, **kwargs): return self._stop()


class GuidedPartialHandler(SafeStopHandler):
    """Grounded explanation/action guidance without unsafe legal drafting.

    Used for P0 workflows whose facts can be organized safely but whose final
    filing or legal position must remain with the taxpayer/professional.
    """
    def __init__(self, category: str):
        self.category = category

    def _requests(self, notice):
        return (notice.get("synthetic_extraction") or {}).get("requests") or []

    def get_questions(self, notice, locale="en", answers=None):
        if self.category == "defective_return_139_9" and not self._requests(notice):
            return {"questions": [], "status": "safe_stop", "supported": False, "reason": "No structured requests were extracted; confirm the notice before guidance."}
        title = "Does the extracted notice summary match your PDF?" if locale == "en" else "निकाले गए नोटिस का सारांश क्या आपके PDF से मेल खाता है?"
        return {"questions": [{"id": "notice_extraction_confirmed", "question_type": "confirmation", "text": title, "help": "We need your confirmation before using extracted facts.", "options": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}, {"id": "unsure", "label": "Not sure"}], "required": True}], "requests": self._requests(notice), "request_count": len(self._requests(notice))}

    def resolve(self, notice, answers, **kwargs):
        answer = answers.get("notice_extraction_confirmed")
        if answer != "yes":
            return {"supported": False, "status": "safe_stop", "reason": "The extracted facts must be confirmed before guidance can continue.", "answers": answers}
        requests = self._requests(notice)
        return {"supported": False, "status": "partial_support", "capability": "PARTIAL_SUPPORT", "workflow_id": self.category, "requests": requests, "missing": ["taxpayer-confirmed defect/figure details", "supporting records where the notice requires them"], "action": "Review the verified notice facts and complete the corresponding action on the official Income Tax e-Filing portal. Seek professional review if the legal position is disputed.", "answers": answers, "handoff_allowed": False}

    def get_evidence(self, notice, statuses=None):
        from app.evidence.mapping import map_evidence
        from app.extraction.notices import extract_notice_requests
        return map_evidence(extract_notice_requests(notice).requests, statuses)

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        return {"status": "approved" if kwargs.get("approved") else "blocked", "handoff_allowed": False, "message": "Professional/taxpayer review is required; Tax Mitra does not submit this communication."}


def get_workflow_handler(category: str | None) -> WorkflowHandler:
    handlers = {
        "income_mismatch_143_1a": IncomeMismatch143Handler(),
        "scrutiny_142_1": Scrutiny142Handler(),
        "defective_return_139_9": GuidedPartialHandler("defective_return_139_9"),
        "income_intimation_143_1": GuidedPartialHandler("income_intimation_143_1"),
    }
    return handlers.get(category, SafeStopHandler())

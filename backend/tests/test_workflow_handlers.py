from app.workflows.handlers import DefectiveReturn1399Handler, IncomeMismatch143Handler, Scrutiny142Handler, SafeStopHandler, get_workflow_handler
from app.routers import workflow as workflow_router


def test_supported_workflows_share_the_handler_contract():
    for handler in (IncomeMismatch143Handler(), Scrutiny142Handler()):
        assert all(callable(getattr(handler, name)) for name in ("get_questions", "resolve", "get_evidence", "generate_response", "review"))


def test_1399_workflow_is_a_real_guided_partial_handler():
    handler = get_workflow_handler("defective_return_139_9")
    assert isinstance(handler, DefectiveReturn1399Handler)
    assert handler.get_questions({})["status"] == "safe_stop"


def test_generic_questions_dispatches_through_resolved_handler(monkeypatch):
    calls = []

    class SpyHandler:
        def get_questions(self, notice, locale="en", answers=None):
            calls.append((notice["id"], locale))
            return {"questions": [{"id": "from-handler"}]}

    monkeypatch.setattr(workflow_router, "get_workflow_handler", lambda category: SpyHandler())
    response = workflow_router.questions("N-2026-001", "hi")
    assert response == {"questions": [{"id": "from-handler"}]}
    assert calls == [("N-2026-001", "hi")]


def test_1399_guides_agree_path_without_inventing_a_legal_response():
    notice = {"synthetic_extraction": {"requests": [
        {"id": "defect-tds", "original_text": "TDS credit has been claimed but corresponding receipts were not offered for taxation.", "page_number": 1},
        {"id": "defect-pan", "original_text": "Name in the ITR does not match the PAN database.", "page_number": 1},
    ]}}
    handler = get_workflow_handler("defective_return_139_9")
    questions = handler.get_questions(notice)["questions"]
    assert {question["id"] for question in questions} == {"defect_extraction_confirmed", "defect_position", "correction_route", "disagreement_reason"}
    assert questions[1]["conditions"] == [{"depends_on": "defect_extraction_confirmed", "equals": "yes"}]
    result = handler.resolve(notice, {"defect_extraction_confirmed": "yes", "defect_position": "agree", "correction_route": "offline_json"})
    assert result["status"] == "partial_support"
    assert "corrected JSON" in result["action"]
    assert "legal conclusion" not in result["draft"]
    assert len(result["checklist"]) == 3


def test_1399_disagree_path_uses_only_taxpayer_remarks_and_not_sure_stops():
    notice = {"synthetic_extraction": {"requests": [{"id": "defect-1", "original_text": "The return is defective because the schedule is incomplete."}]}}
    handler = get_workflow_handler("defective_return_139_9")
    result = handler.resolve(notice, {"defect_extraction_confirmed": "yes", "defect_position": "disagree", "disagreement_reason": "The schedule was completed and filed with the return."})
    assert result["status"] == "partial_support"
    assert "The schedule was completed" in result["draft"]
    unsure = handler.resolve(notice, {"defect_extraction_confirmed": "yes", "defect_position": "unsure"})
    assert unsure["status"] == "safe_stop"

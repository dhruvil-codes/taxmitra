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
    assert response["questions"] == [{"id": "from-handler"}]
    assert "grounding" in response
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


def test_1399_portal_navigation_path():
    """Regression test: 139(9) defective return should navigate to e-Proceedings."""
    notice = {"synthetic_extraction": {"requests": [
        {"id": "defect-tds", "original_text": "TDS credit has been claimed but corresponding receipts were not offered for taxation.", "page_number": 1},
    ]}}
    handler = get_workflow_handler("defective_return_139_9")
    result = handler.resolve(notice, {"defect_extraction_confirmed": "yes", "defect_position": "agree", "correction_route": "online_correction"})
    assert result["status"] == "partial_support"
    assert "portal_navigation_path" in result
    assert result["portal_navigation_path"]["en"] == "e-Proceedings"
    assert result["portal_navigation_path"]["hi"] == "e-Proceedings"


def test_143_1a_resolve_valid_issue_date():
    handler = IncomeMismatch143Handler()
    notice = {
        "id": "notice-valid-date",
        "section": "143(1)(a)",
        "issue_date": "2026-08-13",
        "citizen_id": "c1",
        "official_reference": "DIN-143-TEST",
        "assessment_year": "2025-26",
        "amount_in_question": 45000,
        "income_source": "interest",
    }
    answers = {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"}
    result = handler.resolve(notice, answers)
    assert result["supported"] is True
    assert result["deadline"]["due_date"] == "2026-09-12"
    assert result["deadline"]["days_remaining"] is not None
    assert result["deadline"]["status"] in {"action_required", "due_soon", "expired"}
    assert "2026-08-13" in result["draft"]
    assert "DIN-143-TEST" in result["draft"]


def test_143_1a_resolve_missing_issue_date():
    handler = IncomeMismatch143Handler()
    answers = {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"}

    # Case A: issue_date is explicitly None
    notice_none = {
        "id": "notice-none-date",
        "section": "143(1)(a)",
        "issue_date": None,
        "citizen_id": "c1",
        "official_reference": "DIN-143-NONE",
        "assessment_year": "2025-26",
        "amount_in_question": 45000,
        "income_source": "interest",
    }
    result_none = handler.resolve(notice_none, answers)
    assert result_none["supported"] is True
    assert result_none["deadline"]["due_date"] is None
    assert result_none["deadline"]["days_remaining"] is None
    assert result_none["deadline"]["status"] == "action_required"
    assert "None" not in result_none["draft"]

    # Case B: issue_date key is entirely missing
    notice_missing = {
        "id": "notice-missing-key",
        "section": "143(1)(a)",
        "official_reference": "DIN-143-OMIT",
        "assessment_year": "2025-26",
        "amount_in_question": 45000,
        "income_source": "interest",
    }
    result_missing = handler.resolve(notice_missing, answers)
    assert result_missing["supported"] is True
    assert result_missing["deadline"]["due_date"] is None
    assert result_missing["deadline"]["days_remaining"] is None
    assert result_missing["deadline"]["status"] == "action_required"


def test_143_1a_resolve_malformed_issue_date_preserves_extracted_date():
    handler = IncomeMismatch143Handler()
    answers = {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"}

    # Non-ISO extracted date format like "15/08/2026"
    notice_non_iso = {
        "id": "notice-malformed-date",
        "section": "143(1)(a)",
        "issue_date": "15/08/2026",
        "citizen_id": "c1",
        "official_reference": "DIN-143-MALFORMED",
        "assessment_year": "2025-26",
        "amount_in_question": 45000,
        "income_source": "interest",
    }
    result = handler.resolve(notice_non_iso, answers)
    assert result["supported"] is True
    # Deadline cannot be determined deterministically, so due_date is None
    assert result["deadline"]["due_date"] is None
    assert result["deadline"]["days_remaining"] is None
    assert result["deadline"]["status"] == "action_required"
    # Extracted date is preserved in the draft rather than invented or discarded
    assert "15/08/2026" in result["draft"]

    # Arbitrary non-date string
    notice_garbage = {
        "id": "notice-garbage-date",
        "section": "143(1)(a)",
        "issue_date": "not-a-valid-date",
    }
    result_garbage = handler.resolve(notice_garbage, answers)
    assert result_garbage["supported"] is True
    assert result_garbage["deadline"]["due_date"] is None
    assert result_garbage["deadline"]["days_remaining"] is None
    assert result_garbage["deadline"]["status"] == "action_required"
    assert "not-a-valid-date" in result_garbage["draft"]


def test_143_1a_portal_navigation_path():
    """Regression test: 143(1)(a) income mismatch should navigate to e-Proceedings."""
    handler = IncomeMismatch143Handler()
    notice = {
        "id": "notice-portal-test",
        "section": "143(1)(a)",
        "issue_date": "2026-08-13",
        "citizen_id": "c1",
        "official_reference": "DIN-143-PORTAL",
        "assessment_year": "2025-26",
        "amount_in_question": 45000,
        "income_source": "interest",
    }
    answers = {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"}
    result = handler.resolve(notice, answers)
    assert result["supported"] is True
    assert "portal_navigation_path" in result
    assert result["portal_navigation_path"]["en"] == "e-Proceedings"
    assert result["portal_navigation_path"]["hi"] == "e-Proceedings"


def test_143_1a_real_upload_resolve_via_router_with_null_and_malformed_issue_date():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.extraction.sessions import create_session, confirm_session

    client = TestClient(app)
    answers = {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"}

    # Upload session with None issue_date
    session_id_1, fp1 = create_session({
        "metadata": {
            "section": "143(1)(a)",
            "assessment_year": "2025-26",
            "issue_date": None,
            "response_deadline": None,
            "notice_reference": "DIN-UPLOAD-NONE",
        },
        "pages": [{"page_number": 1, "text": "Notice under section 143(1)(a)"}],
        "notice": {"amount_in_question": 25000, "income_source": "interest"},
    })
    confirm_session(session_id_1, fp1)

    resp1 = client.post("/api/workflow/resolve", json={"notice_id": session_id_1, "answers": answers})
    assert resp1.status_code == 200, resp1.text
    body1 = resp1.json()
    assert body1["supported"] is True
    assert body1["deadline"]["due_date"] is None
    assert body1["deadline"]["days_remaining"] is None
    assert body1["deadline"]["status"] == "action_required"

    # Upload session with malformed issue_date
    session_id_2, fp2 = create_session({
        "metadata": {
            "section": "143(1)(a)",
            "assessment_year": "2025-26",
            "issue_date": "invalid-iso-date",
            "response_deadline": None,
            "notice_reference": "DIN-UPLOAD-MALFORMED",
        },
        "pages": [{"page_number": 1, "text": "Notice under section 143(1)(a)"}],
        "notice": {"amount_in_question": 25000, "income_source": "interest"},
    })
    confirm_session(session_id_2, fp2)

    resp2 = client.post("/api/workflow/resolve", json={"notice_id": session_id_2, "answers": answers})
    assert resp2.status_code == 200, resp2.text
    body2 = resp2.json()
    assert body2["supported"] is True
    assert body2["deadline"]["due_date"] is None
    assert "invalid-iso-date" in body2["draft"]


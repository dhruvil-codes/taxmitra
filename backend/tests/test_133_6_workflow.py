import json
from pathlib import Path

from app.workflows.handlers import InformationRequest1336Handler, get_workflow_handler
from app.workflows.registry import classify_extracted_notice, get_workflow

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_133_6_is_supported_and_uses_shared_handler():
    notice = fixture("information_133_6_business.json")
    assert get_workflow("scrutiny_information_133_6").supported is True
    assert classify_extracted_notice(notice).category == "scrutiny_information_133_6"
    assert isinstance(get_workflow_handler("scrutiny_information_133_6"), InformationRequest1336Handler)


def test_extracts_every_request_with_wording_provenance_and_explanation():
    result = get_workflow_handler("scrutiny_information_133_6").get_questions(fixture("information_133_6_business.json"))
    assert result["request_count"] == 2
    assert result["requests"][0]["original_text"].startswith("Provide a month-wise")
    assert result["requests"][0]["page_number"] == 1
    assert result["requests"][1]["plain_language_explanation"]["en"]


def test_questions_are_minimal_and_support_partial_and_not_sure():
    handler = get_workflow_handler("scrutiny_information_133_6")
    questions = handler.get_questions(fixture("information_133_6_business.json"))["questions"]
    assert len(questions) == 3
    assert {option["id"] for option in questions[1]["options"]} == {"complete", "partial", "unavailable", "not_sure"}
    assert questions[1]["conditions"] == [{"depends_on": "information_record_confirmed", "equals": "yes"}]


def test_evidence_maps_to_each_request():
    checklist = get_workflow_handler("scrutiny_information_133_6").get_evidence(fixture("information_133_6_business.json"))
    assert {item["request_id"] for item in checklist} == {"receipts", "bank-transactions"}
    assert {item["document_id"] for item in checklist} == {"sales-ledger", "bank-statement"}


def test_prepares_structured_partial_response_without_submitting():
    notice = fixture("information_133_6_partial.json")
    result = get_workflow_handler("scrutiny_information_133_6").resolve(notice, {"information_record_confirmed": "yes", "information_status_investment": "partial"})
    assert result["status"] == "supported"
    assert result["response_plan"]["partial_information_allowed"] is True
    assert result["requests"][0]["availability"] == "partial"
    assert result["deadline"] == "2026-10-30"
    assert result["handoff_allowed"] is False
    assert "has not submitted" in result["draft"]


def test_unconfirmed_or_missing_requests_safe_stop():
    handler = get_workflow_handler("scrutiny_information_133_6")
    notice = fixture("information_133_6_business.json")
    assert handler.resolve(notice, {"information_record_confirmed": "unsure"})["status"] == "safe_stop"
    assert handler.resolve({"section": "133(6)", "official_text": "Information notice"}, {})["status"] == "safe_stop"


def test_133_6_portal_navigation_path():
    """Regression test: 133(6) information requests should navigate to e-Proceedings."""
    handler = get_workflow_handler("scrutiny_information_133_6")
    notice = fixture("information_133_6_business.json")
    result = handler.resolve(notice, {"information_record_confirmed": "yes", "information_status_receipts": "complete", "information_status_bank-transactions": "complete"})
    assert result["status"] == "supported"
    assert "portal_navigation_path" in result
    assert result["portal_navigation_path"]["en"] == "e-Proceedings"
    assert result["portal_navigation_path"]["hi"] == "e-Proceedings"

import json
from pathlib import Path

from app.workflows.handlers import AuthorityInformationRequestHandler, ClarificationHandler, get_workflow_handler
from app.workflows.registry import classify_ai_proposal, classify_extracted_notice, get_workflow

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_sectionless_authority_request_uses_generic_fallback():
    notice = fixture("authority_information_request.json")
    result = classify_extracted_notice({**notice, "official_text": "Income Tax Department notice from the Assessing Officer. Please furnish information and documents."})
    assert result.category == "authority_information_request"
    assert result.status == "partial_support"
    assert isinstance(get_workflow_handler(result.category), AuthorityInformationRequestHandler)


def test_ai_authority_fallback_does_not_become_unknown():
    result = classify_ai_proposal({}, {"is_income_tax_communication": True, "category": "unknown_income_tax_communication", "authority_type": "Assessing Officer", "communication_type": "information request", "confidence": 0.92, "reason": "AO requests information"})
    assert result.category == "authority_information_request"
    assert result.status == "partial_support"


def test_clarification_has_distinct_workflow_and_shared_request_contract():
    notice = fixture("authority_clarification.json")
    result = classify_extracted_notice(notice)
    assert result.category == "ao_notice_clarification"
    assert get_workflow("ao_notice_clarification").supported is True
    handler = get_workflow_handler("ao_notice_clarification")
    assert isinstance(handler, ClarificationHandler)
    questions = handler.get_questions(notice)["questions"]
    assert questions[0]["text"].startswith("Do these extracted clarification")
    response = handler.resolve(notice, {"information_record_confirmed": "yes", "information_status_deduction": "complete"})
    assert response["status"] == "supported"
    assert "concise clarification" in response["action"]
    assert response["handoff_allowed"] is False


def test_authority_response_preserves_partial_and_not_sure_boundary():
    notice = fixture("authority_information_request.json")
    handler = get_workflow_handler("authority_information_request")
    response = handler.resolve(notice, {"information_record_confirmed": "yes", "information_status_property-payment": "partial"})
    assert response["status"] == "partial_support"
    assert response["requests"][0]["availability"] == "partial"
    uncertain = handler.resolve(notice, {"information_record_confirmed": "yes", "information_status_property-payment": "not_sure"})
    assert uncertain["status"] == "partial_support"
    assert "remain uncertain" in uncertain["action"]


def test_authority_and_clarification_without_requests_safe_stop():
    assert classify_extracted_notice({"official_text": "Assessing Officer clarification notice"}).status == "safe_stop"
    assert get_workflow_handler("authority_information_request").resolve({"official_text": "AO information request"}, {})["status"] == "safe_stop"

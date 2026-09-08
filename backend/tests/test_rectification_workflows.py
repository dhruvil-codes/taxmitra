import json
from pathlib import Path

from app.workflows.handlers import Rectification154Handler, TaxCreditMismatchHandler, get_workflow_handler
from app.workflows.registry import classify_extracted_notice, get_workflow

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_154_is_supported_and_distinct_from_143_1a():
    assert get_workflow("rectification_154").supported is True
    result = classify_extracted_notice(fixture("rectification_154_reprocess.json"))
    assert result.category == "rectification_154"
    assert classify_extracted_notice({"official_text": "Section 143(1)(a) proposed adjustment"}).category == "income_mismatch_143_1a"


def test_154_supports_each_official_request_type():
    handler = get_workflow_handler("rectification_154")
    assert isinstance(handler, Rectification154Handler)
    for name, expected in (("rectification_154_reprocess.json", "reprocess_return"), ("rectification_154_tax_credit.json", "tax_credit_mismatch"), ("rectification_154_return_data.json", "return_data_correction")):
        notice = fixture(name)
        questions = handler.get_questions(notice)["questions"]
        assert questions[0]["id"] == "rectification_record_confirmed"
        result = handler.resolve(notice, {"rectification_record_confirmed": "yes"})
        assert result["status"] == "supported"
        assert result["path"]["path_id"] == expected
        assert result["handoff_allowed"] is False
        assert result["checklist"]


def test_154_rejects_disagreement_without_record_mistake():
    handler = get_workflow_handler("rectification_154")
    notice = {"section": "154", "rectification_facts": {"issue_type": "reprocess_return", "disagreement_only": True}}
    result = handler.resolve(notice, {"rectification_record_confirmed": "yes", "mistake_apparent": "yes"})
    assert result["status"] == "safe_stop"
    assert "disagrees" in result["reason"]


def test_154_not_sure_and_new_claim_boundary_safe_stop():
    handler = get_workflow_handler("rectification_154")
    notice = fixture("rectification_154_return_data.json")
    assert handler.resolve(notice, {"rectification_record_confirmed": "unsure"})["status"] == "safe_stop"
    new_claim = {"section": "154", "rectification_facts": {"issue_type": "return_data_correction", "mistake_apparent": False}}
    assert handler.resolve(new_claim, {"rectification_record_confirmed": "yes"})["status"] == "safe_stop"


def test_tax_credit_covers_tds_tcs_advance_self_assessment_and_other():
    handler = get_workflow_handler("tax_credit_tds_mismatch")
    assert isinstance(handler, TaxCreditMismatchHandler)
    for filename in ("tax_credit_tds.json", "tax_credit_tcs.json", "tax_credit_advance_tax.json", "tax_credit_self_assessment.json", "tax_credit_other.json"):
        notice = fixture(filename)
        assert handler.get_questions(notice)["facts"]["credit_type"] != "unknown"
        result = handler.resolve(notice, {"credit_record_confirmed": "yes", "correction_owner": "taxpayer"})
        assert result["status"] == "supported"
        assert result["path"]["path_id"] == "taxpayer_correction"
        assert result["facts"].get("amount") is None


def test_tax_credit_deductor_side_and_not_sure_paths():
    handler = get_workflow_handler("tax_credit_tds_mismatch")
    notice = fixture("tax_credit_tds.json")
    result = handler.resolve(notice, {"credit_record_confirmed": "yes", "correction_owner": "deductor"})
    assert result["path"]["path_id"] == "deductor_correction"
    assert "correction" in result["action"].lower()
    unsure = handler.resolve(notice, {"credit_record_confirmed": "yes", "correction_owner": "unsure"})
    assert unsure["status"] == "safe_stop"


def test_tax_credit_requires_confirmation_and_never_invents_values():
    handler = get_workflow_handler("tax_credit_tds_mismatch")
    notice = {"section": "154", "official_text": "Tax credit mismatch in Form 26AS."}
    assert handler.resolve(notice, {"credit_record_confirmed": "no", "correction_owner": "taxpayer"})["status"] == "safe_stop"
    questions = handler.get_questions(notice)["questions"]
    assert any(item["id"] == "credit_type" for item in questions)


def test_154_rectification_portal_navigation_path():
    """Regression test: 154 rectification should navigate to Services → Rectification."""
    handler = get_workflow_handler("rectification_154")
    notice = fixture("rectification_154_reprocess.json")
    result = handler.resolve(notice, {"rectification_record_confirmed": "yes"})
    assert result["status"] == "supported"
    assert "portal_navigation_path" in result
    assert result["portal_navigation_path"]["en"] == "Services → Rectification"
    assert result["portal_navigation_path"]["hi"] == "Services → Rectification"


def test_tax_credit_mismatch_portal_navigation_path():
    """Regression test: Tax credit mismatch should navigate to Services → Rectification."""
    handler = get_workflow_handler("tax_credit_tds_mismatch")
    notice = fixture("tax_credit_tds.json")
    result = handler.resolve(notice, {"credit_record_confirmed": "yes", "correction_owner": "taxpayer"})
    assert result["status"] == "supported"
    assert "portal_navigation_path" in result
    assert result["portal_navigation_path"]["en"] == "Services → Rectification"
    assert result["portal_navigation_path"]["hi"] == "Services → Rectification"

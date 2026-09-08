import json
from pathlib import Path

from app.workflows.handlers import Demand245Handler, get_workflow_handler
from app.workflows.registry import classify_extracted_notice, get_workflow

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_section_245_and_outstanding_demand_are_supported():
    assert get_workflow("demand_adjustment_245").supported is True
    assert get_workflow("outstanding_tax_demand").supported is True
    assert classify_extracted_notice(fixture("demand_245_correct_unpaid.json")).category == "demand_adjustment_245"


def test_correct_unpaid_routes_to_portal_payment_without_paying():
    handler = get_workflow_handler("demand_adjustment_245")
    assert isinstance(handler, Demand245Handler)
    notice = fixture("demand_245_correct_unpaid.json")
    result = handler.resolve(notice, {"demand_record_confirmed": "yes", "demand_status": "correct_unpaid"})
    assert result["status"] == "supported"
    assert "will not initiate payment" in result["action"]
    assert result["handoff_allowed"] is False


def test_correct_paid_requires_challan_evidence():
    handler = get_workflow_handler("demand_adjustment_245")
    notice = fixture("demand_245_correct_paid.json")
    result = handler.resolve(notice, {"demand_record_confirmed": "yes", "demand_status": "correct_paid", "payment_evidence": "no"})
    assert result["status"] == "safe_stop"
    result = handler.resolve(notice, {"demand_record_confirmed": "yes", "demand_status": "correct_paid", "payment_evidence": "yes"})
    assert result["status"] == "supported"
    assert any(item["document_id"] == "245-payment-record" for item in result["checklist"])


def test_full_dispute_requires_reasons_and_supporting_details():
    handler = get_workflow_handler("demand_adjustment_245")
    notice = fixture("demand_245_full_dispute.json")
    result = handler.resolve(notice, {"demand_record_confirmed": "yes", "demand_status": "disputed_full", "dispute_reasons": ["previous_processing_error"], "dispute_details": "The earlier processing record did not include the payment."})
    assert result["status"] == "supported"
    assert "full disagreement" in result["action"]
    assert result["handoff_allowed"] is False


def test_partial_dispute_requires_undisputed_amount_and_preserves_official_boundary():
    handler = get_workflow_handler("demand_adjustment_245")
    notice = fixture("demand_245_partial_dispute.json")
    base = {"demand_record_confirmed": "yes", "demand_status": "disputed_partial", "dispute_reasons": ["previous_processing_error"], "dispute_details": "Part of the demand is based on a processing error."}
    missing = handler.resolve(notice, base)
    assert missing["status"] == "safe_stop"
    result = handler.resolve(notice, {**base, "undisputed_amount": "12000"})
    assert result["status"] == "supported"
    assert "undisputed amount" in result["action"]
    assert "paid before submitting" in result["action"]


def test_guided_choices_and_multi_select_are_dynamic():
    handler = get_workflow_handler("demand_adjustment_245")
    questions = handler.get_questions(fixture("demand_245_full_dispute.json"))["questions"]
    status = next(item for item in questions if item["id"] == "demand_status")
    reasons = next(item for item in questions if item["id"] == "dispute_reasons")
    assert {item["id"] for item in status["options"]} >= {"correct_unpaid", "correct_paid", "disputed_full", "disputed_partial", "unsure"}
    assert reasons["question_type"] == "multi_choice"


def test_not_sure_and_missing_amount_never_create_payment_or_response():
    handler = get_workflow_handler("demand_adjustment_245")
    notice = fixture("demand_245_challan.json")
    unsure = handler.resolve(notice, {"demand_record_confirmed": "yes", "demand_status": "unsure"})
    assert unsure["status"] == "safe_stop"
    no_amount = handler.resolve({"section": "245", "official_text": "Outstanding demand under section 245."}, {"demand_record_confirmed": "yes", "demand_status": "correct_unpaid"})
    assert no_amount["status"] == "safe_stop"


def test_245_demand_portal_navigation_path():
    """Regression test: 245 demand should navigate to Pending Actions → Response to Outstanding Demand."""
    handler = get_workflow_handler("demand_adjustment_245")
    notice = fixture("demand_245_correct_unpaid.json")
    result = handler.resolve(notice, {"demand_record_confirmed": "yes", "demand_status": "correct_unpaid"})
    assert result["status"] == "supported"
    assert "portal_navigation_path" in result
    assert result["portal_navigation_path"]["en"] == "Pending Actions → Response to Outstanding Demand"
    assert result["portal_navigation_path"]["hi"] == "Pending Actions → Response to Outstanding Demand"

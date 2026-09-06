import json
from pathlib import Path

from app.workflows.handlers import IncomeIntimation143Handler, get_workflow_handler
from app.workflows.registry import WorkflowCapability, classify_extracted_notice, get_workflow


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_registry_marks_143_1_supported_and_keeps_143_1a_distinct():
    definition = get_workflow("income_intimation_143_1")
    assert definition is not None
    assert definition.capability is WorkflowCapability.SUPPORTED
    general = classify_extracted_notice(load_fixture("intimation_143_1_refund.json"))
    adjustment = classify_extracted_notice({"official_text": "Intimation under section 143(1)(a): proposed adjustment."})
    assert general.category == "income_intimation_143_1"
    assert general.status == "supported"
    assert adjustment.category == "income_mismatch_143_1a"


def test_refund_path_routes_received_or_refund_reissue_without_submission():
    handler = get_workflow_handler("income_intimation_143_1")
    assert isinstance(handler, IncomeIntimation143Handler)
    notice = load_fixture("intimation_143_1_refund.json")
    questions = handler.get_questions(notice)["questions"]
    assert {item["id"] for item in questions} == {"intimation_facts_confirmed", "refund_received"}
    result = handler.resolve(notice, {"intimation_facts_confirmed": "yes", "refund_received": "no"})
    assert result["status"] == "supported"
    assert "Refund Reissue" in result["action"]
    assert result["handoff_allowed"] is False


def test_demand_and_tax_calculation_difference_route_to_reviewable_rectification():
    handler = get_workflow_handler("income_intimation_143_1")
    for filename in ("intimation_143_1_demand.json", "intimation_143_1_calculation_difference.json"):
        notice = load_fixture(filename)
        result = handler.resolve(notice, {"intimation_facts_confirmed": "yes", "intimation_action": "rectification"})
        assert result["status"] == "supported"
        assert result["path"]["path_id"] == "rectification"
        assert result["handoff_allowed"] is False
        assert result["checklist"]


def test_tds_mismatch_routes_to_tax_credit_correction_and_preserves_evidence():
    handler = get_workflow_handler("income_intimation_143_1")
    notice = load_fixture("intimation_143_1_tds_mismatch.json")
    questions = handler.get_questions(notice)["questions"]
    action_question = next(item for item in questions if item["id"] == "intimation_action")
    assert {option["id"] for option in action_question["options"]} >= {"tax_credit", "unsure"}
    result = handler.resolve(notice, {"intimation_facts_confirmed": "yes", "intimation_action": "tax_credit"})
    assert result["path"]["path_id"] == "tax_credit_mismatch"
    assert any(item["document_id"] == "143-1-tax-credit-records" for item in result["checklist"])


def test_no_action_outcome_does_not_ask_unnecessary_questions():
    handler = get_workflow_handler("income_intimation_143_1")
    notice = load_fixture("intimation_143_1_no_action.json")
    questions = handler.get_questions(notice)["questions"]
    assert [item["id"] for item in questions] == ["intimation_facts_confirmed"]
    result = handler.resolve(notice, {"intimation_facts_confirmed": "yes"})
    assert result["outcome"] == "no_action"
    assert "No follow-up action" in result["action"]


def test_not_sure_never_becomes_an_action():
    handler = get_workflow_handler("income_intimation_143_1")
    notice = load_fixture("intimation_143_1_demand.json")
    result = handler.resolve(notice, {"intimation_facts_confirmed": "yes", "intimation_action": "unsure"})
    assert result["status"] == "safe_stop"
    assert result["handoff_allowed"] is False


def test_missing_processed_outcome_safe_stops_instead_of_inventing():
    handler = get_workflow_handler("income_intimation_143_1")
    notice = {"section": "143(1)", "official_text": "The return was processed."}
    questions = handler.get_questions(notice)
    assert questions["status"] == "safe_stop"
    assert handler.resolve(notice, {})["status"] == "safe_stop"


def test_uploaded_text_can_route_an_explicit_outcome_without_fabricating_figures():
    handler = get_workflow_handler("income_intimation_143_1")
    notice = {
        "section": "143(1)",
        "official_text": "Income Tax Department. Final intimation under section 143(1). Refund determined at Rs. 8,500.",
    }
    contract = handler.get_questions(notice)
    assert contract["outcome"] == "refund"
    assert "refund_received" in {item["id"] for item in contract["questions"]}
    result = handler.resolve(notice, {"intimation_facts_confirmed": "yes", "refund_received": "yes"})
    assert result["status"] == "supported"
    assert result["facts"].get("refund_amount") is None

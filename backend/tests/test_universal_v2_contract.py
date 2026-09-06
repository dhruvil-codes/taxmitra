from app.workflows.handlers import GuidedPartialHandler, get_workflow_handler
from app.workflows.registry import WorkflowCapability, classify_extracted_notice, get_workflow, list_workflows


def test_registry_covers_required_taxonomy_and_explicit_capabilities():
    categories = {item["category"]: item for item in list_workflows()}
    required = {"defective_return_139_9", "income_intimation_143_1", "income_mismatch_143_1a", "scrutiny_142_1", "scrutiny_information_133_6", "rectification_154", "tax_credit_tds_mismatch", "demand_adjustment_245", "reassessment_148", "reassessment_148a", "penalty_proceedings", "unknown_income_tax_communication"}
    assert required <= categories.keys()
    assert {item["capability"] for item in categories.values()} == {"SUPPORTED", "PARTIAL_SUPPORT", "EXPLANATION_ONLY", "SAFE_STOP"}


def test_classification_returns_evidence_and_distinguishes_general_143_from_adjustment():
    general = classify_extracted_notice({"official_text": "Intimation under section 143(1). Return processed; refund determined."})
    adjustment = classify_extracted_notice({"official_text": "Communication under section 143(1)(a). Proposed adjustment to income."})
    assert general.category == "income_intimation_143_1"
    assert adjustment.category == "income_mismatch_143_1a"
    assert general.evidence and adjustment.evidence
    assert adjustment.capability == WorkflowCapability.SUPPORTED.value


def test_high_risk_and_ambiguous_content_safe_stop_without_response():
    reassessment = classify_extracted_notice({"official_text": "Notice under section 148A show cause proceeding."})
    ambiguous = classify_extracted_notice({"official_text": "Assessing Officer clarification about rectification."})
    assert reassessment.status == "safe_stop"
    assert reassessment.capability == "SAFE_STOP"
    assert ambiguous.status == "safe_stop"


def test_p0_partial_handler_requires_confirmation_and_preserves_requests():
    notice = {"synthetic_extraction": {"requests": [{"id": "r1", "original_text": "Remove the defect shown in the return.", "response_section": "139(9)", "page_number": 2}]}}
    handler = get_workflow_handler("defective_return_139_9")
    assert isinstance(handler, GuidedPartialHandler)
    assert handler.get_questions(notice)["request_count"] == 1
    assert handler.resolve(notice, {"notice_extraction_confirmed": "unsure"})["status"] == "safe_stop"
    result = handler.resolve(notice, {"notice_extraction_confirmed": "yes"})
    assert result["status"] == "partial_support"
    assert result["requests"][0]["original_text"].startswith("Remove")

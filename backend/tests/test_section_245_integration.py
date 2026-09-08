"""End-to-end integration test for Section 245 demand workflow routing."""

import pytest
from app.rules.notice_types import classify_notice, NoticeCategory, is_supported
from app.workflows.registry import classify_extracted_notice, get_workflow
from app.workflows.handlers import Demand245Handler, get_workflow_handler


def test_section_245_dashboard_classification():
    """Test that Section 245 appears as supported in dashboard classification."""
    notice = {"section": "245", "official_text": "Income Tax Department outstanding demand under section 245."}
    category = classify_notice(notice)
    
    # Should classify to DEMAND_ADJUSTMENT_245, not UNSUPPORTED
    assert category == NoticeCategory.DEMAND_ADJUSTMENT_245
    assert category != NoticeCategory.UNSUPPORTED
    
    # Should be marked as supported
    assert is_supported(category)


def test_section_245_upload_classification():
    """Test that Section 245 upload extraction classifies correctly."""
    extracted_notice = {
        "section": "245",
        "official_text": "Income Tax Department. Outstanding demand notice under section 245. Demand amount: ₹50,000 for AY 2025-26.",
        "synthetic_extraction": {
            "requests": [
                {"original_text": "Pay the outstanding demand of ₹50,000", "response_section": "demand_payment"}
            ]
        }
    }
    
    result = classify_extracted_notice(extracted_notice)
    
    # Should classify to demand_adjustment_245
    assert result.category == "demand_adjustment_245"
    assert result.supported is True
    assert result.capability == "SUPPORTED"
    # Check that evidence contains section reference
    assert any(e["kind"] == "section_reference" and "245" in e["value"] for e in result.evidence)


def test_section_245_workflow_routing():
    """Test that Section 245 routes to the correct workflow handler."""
    workflow = get_workflow("demand_adjustment_245")
    
    # Should be supported and have correct metadata
    assert workflow is not None
    assert workflow.supported is True
    assert workflow.category == "demand_adjustment_245"
    assert workflow.capability.value == "SUPPORTED"
    assert workflow.frontend_entry == "journey"
    
    # Should route to Demand245Handler
    handler = get_workflow_handler("demand_adjustment_245")
    assert isinstance(handler, Demand245Handler)


def test_section_245_questions_generation():
    """Test that Section 245 generates appropriate questions."""
    notice = {
        "section": "245",
        "official_text": "Income Tax Department outstanding demand under section 245. Demand amount: ₹50,000 for AY 2025-26.",
        "demand_amount": "50000",
        "assessment_year": "2025-26"
    }
    
    handler = get_workflow_handler("demand_adjustment_245")
    questions_result = handler.get_questions(notice)
    
    # Should have questions
    assert "questions" in questions_result
    questions = questions_result["questions"]
    assert len(questions) > 0
    
    # Should have key demand-related questions
    question_ids = {q["id"] for q in questions}
    assert "demand_record_confirmed" in question_ids
    assert "demand_status" in question_ids


def test_section_245_response_action_plan():
    """Test that Section 245 generates appropriate response/action plans."""
    notice = {
        "section": "245",
        "official_text": "Income Tax Department outstanding demand under section 245. Demand amount: ₹50,000 for AY 2025-26.",
        "demand_amount": "50000",
        "assessment_year": "2025-26"
    }
    
    handler = get_workflow_handler("demand_adjustment_245")
    
    # Test correct unpaid scenario
    result = handler.resolve(notice, {
        "demand_record_confirmed": "yes",
        "demand_status": "correct_unpaid"
    })

    # Unpaid demands may route to safe_stop for safety
    assert result["status"] in ["supported", "safe_stop"]
    assert result["handoff_allowed"] is False  # Never auto-submit
    # If safe_stop, should have reason; if supported, should have action
    if result["status"] == "safe_stop":
        assert "reason" in result
    else:
        assert "action" in result


def test_section_245_safe_stop_behavior():
    """Test that Section 245 maintains existing safe-stop behavior for edge cases."""
    handler = get_workflow_handler("demand_adjustment_245")
    
    # Test "not sure" scenario should safe-stop
    notice = {
        "section": "245",
        "official_text": "Income Tax Department outstanding demand under section 245."
    }
    result = handler.resolve(notice, {
        "demand_record_confirmed": "yes",
        "demand_status": "unsure"
    })
    assert result["status"] == "safe_stop"
    
    # Test missing amount should safe-stop
    result = handler.resolve(notice, {
        "demand_record_confirmed": "yes",
        "demand_status": "correct_unpaid"
    })
    assert result["status"] == "safe_stop"
    
    # Test partial dispute without undisputed amount should safe-stop
    notice_with_amount = {
        "section": "245",
        "official_text": "Income Tax Department outstanding demand under section 245. Demand amount: ₹50,000.",
        "demand_amount": "50000"
    }
    result = handler.resolve(notice_with_amount, {
        "demand_record_confirmed": "yes",
        "demand_status": "disputed_partial",
        "dispute_reasons": ["processing_error"],
        "dispute_details": "Processing error in calculation"
    })
    assert result["status"] == "safe_stop"


def test_section_245_registry_integration():
    """Test that Section 245 is properly integrated in the workflow registry."""
    from app.workflows.registry import list_workflows
    
    workflows = list_workflows()
    
    # Find demand_adjustment_245 workflow
    demand_245 = next((w for w in workflows if w["category"] == "demand_adjustment_245"), None)
    
    assert demand_245 is not None
    assert demand_245["supported"] is True
    assert demand_245["capability"] == "SUPPORTED"
    assert demand_245["frontend_entry"] == "journey"
    
    # Verify classification signals include 245
    assert any("245" in signal for signal in demand_245["classification_signals"])


def test_section_245_various_text_patterns():
    """Test that various Section 245 text patterns classify correctly."""
    test_cases = [
        "Section 245 demand adjustment notice",
        "Outstanding demand under section 245",
        "Adjustment against demand under section 245",
        "Refund adjusted against previous demand - section 245",
        "Demand notice u/s 245"
    ]
    
    for text in test_cases:
        notice = {"section": "245", "official_text": text}
        result = classify_extracted_notice(notice)
        assert result.category == "demand_adjustment_245", f"Failed for text: {text}"
        assert result.supported is True


def test_section_245_no_duplicate_workflow():
    """Test that there's no duplicate workflow for Section 245."""
    from app.workflows.registry import list_workflows
    
    workflows = list_workflows()
    demand_245_workflows = [w for w in workflows if "245" in w["category"].lower()]
    
    # Should only have one 245-related workflow
    assert len(demand_245_workflows) == 1
    assert demand_245_workflows[0]["category"] == "demand_adjustment_245"

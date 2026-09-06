"""Universal notice engine routing and safe-stop coverage."""

from fastapi.testclient import TestClient

from app.main import app
from app.workflows.registry import classify_extracted_notice, list_workflows


client = TestClient(app)


def test_registry_contains_initial_workflow_implementations_and_safe_stops():
    workflows = {item["workflow_id"]: item for item in list_workflows()}

    assert {
        "income_mismatch_143_1a",
        "scrutiny_142_1",
        "defective_return_139_9",
        "rectification_tax_credit_mismatch",
        "ao_notice_clarification",
    } <= workflows.keys()
    assert workflows["income_mismatch_143_1a"]["supported"] is True
    assert workflows["scrutiny_142_1"]["supported"] is True
    assert workflows["defective_return_139_9"]["status"] == "safe_stop"


def test_extracted_content_routes_without_structured_section_and_stops_low_confidence():
    result = classify_extracted_notice({"official_text": "Notice under section 139(9). Please remove the defects in the return."})
    assert result.workflow_id == "defective_return_139_9"
    assert result.supported is False
    assert result.status == "safe_stop"

    ambiguous = classify_extracted_notice({"official_text": "AO notice concerning rectification."})
    assert ambiguous.status == "safe_stop"
    assert ambiguous.category == "ambiguous"

    low_grounding = classify_extracted_notice(
        {"section": "142(1)"},
        {"below_floor": True, "verified": False},
    )
    assert low_grounding.status == "safe_stop"
    assert low_grounding.reason == "classification grounding is below the safe floor"

    low_confidence_grounding = classify_extracted_notice(
        {"section": "143(1)(a)"},
        {"confidence": 0.4, "verified": False},
    )
    assert low_confidence_grounding.status == "safe_stop"


def test_generic_workflow_api_is_additive_and_notice_metadata_is_generic():
    catalog = client.get("/api/workflows")
    assert catalog.status_code == 200
    assert any(item["workflow_id"] == "scrutiny_142_1" for item in catalog.json()["workflows"])

    card = client.get("/api/notices/N-2026-003").json()
    assert card["workflow_id"] == "scrutiny_142_1"
    assert card["workflow_status"] == "supported"
    assert card["classification_confidence"] == 1.0

    routed = client.get("/api/notices/N-2026-002/workflow")
    assert routed.status_code == 200
    assert routed.json()["classification"]["status"] == "safe_stop"
    assert routed.json()["classification"]["category"] == "unsupported"
    assert routed.json()["workflow"] is None


def test_classified_frontend_entries_route_supported_and_safe_stop_workflows():
    assert classify_extracted_notice({"section": "143(1)(a)"}).payload()["status"] == "supported"
    assert classify_extracted_notice({"section": "142(1)"}).payload()["status"] == "supported"
    for notice in (
        {"section": "139(9)"},
        {"official_text": "rectification under section 154"},
        {"official_text": "Assessing Officer clarification notice"},
    ):
        result = classify_extracted_notice(notice)
        assert result.status == "safe_stop"
        assert result.supported is False

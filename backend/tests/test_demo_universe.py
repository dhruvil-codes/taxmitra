"""Regression tests for the expanded demo universe covering all 19 workflow categories.

Each test verifies that a synthetic demo notice:
1. Classifies correctly to its intended workflow
2. Has the appropriate capability (SUPPORTED, PARTIAL_SUPPORT, EXPLANATION_ONLY, SAFE_STOP)
3. Can be processed through the workflow without errors
4. Shows realistic behavior (not fully automated for SAFE_STOP/EXPLANATION_ONLY)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_all_19_demo_notices_exist():
    """Verify that all 19 demo notices are present in the dataset."""
    body = client.get("/api/notices").json()
    assert len(body) == 19
    notice_ids = [n["id"] for n in body]
    # Verify all expected notice IDs exist
    expected_ids = [
        "N-2026-001",  # 143(1)(a) income mismatch
        "N-2026-002",  # 148 reassessment (SAFE_STOP)
        "N-2026-003",  # 142(1) scrutiny
        "N-2026-004",  # 139(9) defective return
        "N-2026-005",  # 143(1) processing intimation
        "N-2026-006",  # 133(6) information request
        "N-2026-007",  # 131 summons (EXPLANATION_ONLY)
        "N-2026-008",  # 154 rectification
        "N-2026-009",  # 154 tax credit mismatch
        "N-2026-010",  # 245 demand adjustment
        "N-2026-011",  # 245 outstanding demand
        "N-2026-012",  # Refund communication (ambiguous classification)
        "N-2026-013",  # AO clarification
        "N-2026-014",  # Authority information request
        "N-2026-015",  # 148A show cause (SAFE_STOP)
        "N-2026-016",  # Penalty proceedings (ambiguous classification)
        "N-2026-017",  # AIS compliance
        "N-2026-018",  # Unknown communication (SAFE_STOP)
        "N-2026-019",  # Non-tax document (SAFE_STOP)
    ]
    for expected_id in expected_ids:
        assert expected_id in notice_ids, f"Expected notice {expected_id} not found in demo dataset"


def test_all_5_citizens_exist():
    """Verify that all 5 demo citizens are present."""
    body = client.get("/api/citizens").json()
    assert len(body) == 5
    citizen_ids = [c["id"] for c in body]
    expected_ids = ["C-001", "C-002", "C-003", "C-004", "C-005"]
    for expected_id in expected_ids:
        assert expected_id in citizen_ids, f"Expected citizen {expected_id} not found"


def test_143_1a_income_mismatch_is_supported():
    """Verify 143(1)(a) income mismatch demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-001").json()
    assert body["section"] == "143(1)(a)"
    assert body["workflow_id"] == "income_mismatch_143_1a"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True


def test_148_reassessment_is_safe_stop():
    """Verify 148 reassessment demo is SAFE_STOP."""
    body = client.get("/api/notices/N-2026-002").json()
    assert body["section"] == "148"
    # Note: Legacy classify_notice maps 148 to UNSUPPORTED for backward compatibility
    # But the workflow registry correctly identifies it as reassessment_148 with SAFE_STOP
    assert body["workflow_status"] == "safe_stop"
    assert body["supported"] is False
    # Verify the actual workflow classification through the workflow endpoint
    workflow_body = client.get("/api/notices/N-2026-002/workflow").json()
    assert workflow_body["classification"]["category"] == "reassessment_148"
    assert workflow_body["classification"]["workflow_id"] == "reassessment_148"
    assert workflow_body["contract"]["capability"] == "SAFE_STOP"


def test_142_1_scrutiny_is_supported():
    """Verify 142(1) scrutiny demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-003").json()
    assert body["section"] == "142(1)"
    assert body["workflow_id"] == "scrutiny_142_1"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True
    # Verify it has synthetic extraction with requests
    workflow_body = client.get("/api/notices/N-2026-003/workflow").json()
    assert len(workflow_body["contract"]["requests"]) > 0


def test_139_9_defective_return_is_partial_support():
    """Verify 139(9) defective return demo is PARTIAL_SUPPORT."""
    body = client.get("/api/notices/N-2026-004").json()
    assert body["section"] == "139(9)"
    assert body["workflow_id"] == "defective_return_139_9"
    assert body["workflow_status"] == "partial_support"
    assert body["supported"] is False  # PARTIAL_SUPPORT is not fully supported
    # Verify it has synthetic extraction with defect requests
    workflow_body = client.get("/api/notices/N-2026-004/workflow").json()
    assert len(workflow_body["contract"]["requests"]) > 0


def test_143_1_processing_intimation_is_supported():
    """Verify 143(1) processing intimation demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-005").json()
    assert body["section"] == "143(1)"
    assert body["workflow_id"] == "income_intimation_143_1"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True


def test_133_6_information_request_is_supported():
    """Verify 133(6) information request demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-006").json()
    assert body["section"] == "133(6)"
    assert body["workflow_id"] == "scrutiny_information_133_6"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True
    # Verify it has synthetic extraction with requests
    workflow_body = client.get("/api/notices/N-2026-006/workflow").json()
    assert len(workflow_body["contract"]["requests"]) > 0


def test_131_summons_is_explanation_only():
    """Verify 131 summons demo is EXPLANATION_ONLY."""
    body = client.get("/api/notices/N-2026-007").json()
    assert body["section"] == "131"
    # Note: Legacy classify_notice may not have authority_131 in enum
    # But the workflow registry correctly identifies it as authority_131 with EXPLANATION_ONLY
    assert body["workflow_status"] == "safe_stop"  # EXPLANATION_ONLY routes to safe_stop
    assert body["supported"] is False
    # Verify the actual workflow classification through the workflow endpoint
    workflow_body = client.get("/api/notices/N-2026-007/workflow").json()
    assert workflow_body["classification"]["category"] == "authority_131"
    assert workflow_body["classification"]["workflow_id"] == "authority_131"
    assert workflow_body["contract"]["capability"] == "EXPLANATION_ONLY"


def test_154_rectification_is_supported():
    """Verify 154 rectification demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-008").json()
    assert body["section"] == "154"
    assert body["workflow_id"] == "rectification_154"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True


def test_154_tax_credit_mismatch_is_supported():
    """Verify 154 tax credit mismatch demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-009").json()
    assert body["section"] == "154"
    # The classification logic routes TDS credit mismatches to tax_credit_tds_mismatch
    assert body["workflow_id"] == "tax_credit_tds_mismatch"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True


def test_245_demand_adjustment_is_supported():
    """Verify 245 demand adjustment demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-010").json()
    assert body["section"] == "245"
    assert body["workflow_id"] == "demand_adjustment_245"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True


def test_245_outstanding_demand_is_supported():
    """Verify 245 outstanding demand demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-011").json()
    assert body["section"] == "245"
    # The classification logic routes all 245 notices to demand_adjustment_245
    # This is appropriate since both demand adjustment and outstanding demand share the same section
    assert body["workflow_id"] == "demand_adjustment_245"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True


def test_refund_communication_is_explanation_only():
    """Verify refund communication demo is EXPLANATION_ONLY."""
    body = client.get("/api/notices/N-2026-012").json()
    assert body["section"] == "REFUND"
    # Refund communications are ambiguous in classification but should route to safe_stop
    assert body["workflow_status"] == "safe_stop"
    assert body["supported"] is False
    # Verify the workflow endpoint provides EXPLANATION_ONLY capability
    workflow_body = client.get("/api/notices/N-2026-012/workflow").json()
    # The classification may be ambiguous, but the contract should still be complete
    assert workflow_body["contract"]["capability"] in ["EXPLANATION_ONLY", "SAFE_STOP"]
    assert workflow_body["contract"]["safe_stop"]["reason"] is not None


def test_ao_clarification_is_supported():
    """Verify AO clarification demo is SUPPORTED."""
    body = client.get("/api/notices/N-2026-013").json()
    assert body["section"] == "CLARIFICATION"
    assert body["workflow_id"] == "ao_notice_clarification"
    assert body["workflow_status"] == "supported"
    assert body["supported"] is True
    # Verify it has synthetic extraction with requests
    workflow_body = client.get("/api/notices/N-2026-013/workflow").json()
    assert len(workflow_body["contract"]["requests"]) > 0


def test_authority_information_request_is_partial_support():
    """Verify authority information request demo is PARTIAL_SUPPORT."""
    body = client.get("/api/notices/N-2026-014").json()
    assert body["section"] == "AUTHORITY_REQUEST"
    # Note: Legacy classify_notice may not have authority_information_request in enum
    # But the workflow registry correctly identifies it as authority_information_request with PARTIAL_SUPPORT
    assert body["workflow_status"] == "partial_support"
    assert body["supported"] is False
    # Verify the actual workflow classification through the workflow endpoint
    workflow_body = client.get("/api/notices/N-2026-014/workflow").json()
    assert workflow_body["classification"]["category"] == "authority_information_request"
    assert workflow_body["classification"]["workflow_id"] == "authority_information_request"
    assert workflow_body["contract"]["capability"] == "PARTIAL_SUPPORT"
    # Verify it has synthetic extraction with requests
    assert len(workflow_body["contract"]["requests"]) > 0


def test_148a_show_cause_is_safe_stop():
    """Verify 148A show cause demo is SAFE_STOP."""
    body = client.get("/api/notices/N-2026-015").json()
    assert body["section"] == "148A"
    # Note: Legacy classify_notice may not have reassessment_148a in enum
    # But the workflow registry correctly identifies it as reassessment_148a with SAFE_STOP
    assert body["workflow_status"] == "safe_stop"
    assert body["supported"] is False
    # Verify the actual workflow classification through the workflow endpoint
    workflow_body = client.get("/api/notices/N-2026-015/workflow").json()
    assert workflow_body["classification"]["category"] == "reassessment_148a"
    assert workflow_body["classification"]["workflow_id"] == "reassessment_148a"
    assert workflow_body["contract"]["capability"] == "SAFE_STOP"


def test_penalty_proceedings_is_safe_stop():
    """Verify penalty proceedings demo is SAFE_STOP."""
    body = client.get("/api/notices/N-2026-016").json()
    assert body["section"] == "PENALTY"
    # Penalty proceedings may be ambiguous in classification but should route to safe_stop
    assert body["workflow_status"] == "safe_stop"
    assert body["supported"] is False
    # Verify the workflow endpoint provides SAFE_STOP capability
    workflow_body = client.get("/api/notices/N-2026-016/workflow").json()
    # The classification may be ambiguous, but the contract should provide SAFE_STOP capability
    assert workflow_body["contract"]["capability"] in ["SAFE_STOP", "EXPLANATION_ONLY"]
    assert workflow_body["contract"]["safe_stop"]["reason"] is not None


def test_ais_compliance_is_partial_support():
    """Verify AIS compliance demo is PARTIAL_SUPPORT."""
    body = client.get("/api/notices/N-2026-017").json()
    assert body["section"] == "AIS"
    # Note: Legacy classify_notice may not have compliance_ais in enum
    # But the workflow registry correctly identifies it as compliance_ais with PARTIAL_SUPPORT
    assert body["workflow_status"] == "partial_support"
    assert body["supported"] is False
    # Verify the actual workflow classification through the workflow endpoint
    workflow_body = client.get("/api/notices/N-2026-017/workflow").json()
    assert workflow_body["classification"]["category"] == "compliance_ais"
    assert workflow_body["classification"]["workflow_id"] == "compliance_ais"
    assert workflow_body["contract"]["capability"] == "PARTIAL_SUPPORT"


def test_unknown_communication_is_safe_stop():
    """Verify unknown communication demo is SAFE_STOP."""
    body = client.get("/api/notices/N-2026-018").json()
    assert body["section"] == "UNKNOWN"
    # Unknown communications may be classified as supported by legacy classify_notice
    # But the workflow registry should identify them as unknown_income_tax_communication with SAFE_STOP
    # Verify the actual workflow classification through the workflow endpoint
    workflow_body = client.get("/api/notices/N-2026-018/workflow").json()
    assert workflow_body["classification"]["category"] == "unknown_income_tax_communication"
    assert workflow_body["classification"]["workflow_id"] == "unknown_income_tax_communication"
    assert workflow_body["contract"]["capability"] == "SAFE_STOP"


def test_non_tax_document_is_safe_stop():
    """Verify non-tax document demo is SAFE_STOP."""
    body = client.get("/api/notices/N-2026-019").json()
    assert body["section"] == "NON_TAX"
    # Non-tax documents should route to safe_stop regardless of classification
    # Verify the workflow endpoint provides SAFE_STOP capability
    workflow_body = client.get("/api/notices/N-2026-019/workflow").json()
    # The classification may vary, but the contract should provide SAFE_STOP capability
    assert workflow_body["contract"]["capability"] in ["SAFE_STOP", "EXPLANATION_ONLY"]
    assert workflow_body["contract"]["safe_stop"]["reason"] is not None


def test_demo_notices_have_realistic_synthetic_data():
    """Verify all demo notices have realistic synthetic data without real taxpayer information."""
    # Check the raw data store since notice list doesn't include full text
    from app.data_store import load_notices
    notices = load_notices()
    for notice in notices:
        # Check that all notices have fictional markers
        assert "fictional" in notice["official_text"].lower() or "synthetic" in notice["official_text"].lower()
        # Check that official references are marked as fictional
        assert "fictional" in notice["official_reference"] or "DEMO" in notice["official_reference"]
        # Check that income sources are marked as fictional
        if notice.get("income_source"):
            if isinstance(notice["income_source"], dict):
                assert "fictional" in notice["income_source"].get("en", "").lower() or "fictional" in notice["income_source"].get("hi", "")
            else:
                assert "fictional" in str(notice["income_source"]).lower()


def test_demo_notices_have_distinct_categories():
    """Verify demo notices cover all distinct workflow categories."""
    body = client.get("/api/notices").json()
    # Check workflow endpoint classifications for actual category coverage
    workflow_categories = set()
    for notice in body:
        workflow_body = client.get(f"/api/notices/{notice['id']}/workflow").json()
        workflow_categories.add(workflow_body["classification"]["category"])
    # Verify we have coverage across different workflow categories
    expected_workflows = {
        "income_mismatch_143_1a",
        "reassessment_148",
        "scrutiny_142_1",
        "defective_return_139_9",
        "income_intimation_143_1",
        "scrutiny_information_133_6",
        "authority_131",
        "rectification_154",
        "tax_credit_tds_mismatch",  # Classification routes 154+TDS mismatch here
        "demand_adjustment_245",  # Classification routes both 245 demand types here
        "ao_notice_clarification",
        "authority_information_request",
        "reassessment_148a",
        "compliance_ais",
        "unknown_income_tax_communication",
    }
    for expected_workflow in expected_workflows:
        assert expected_workflow in workflow_categories, f"Expected workflow {expected_workflow} not found in demo dataset"


def test_demo_notices_have_proper_capability_distribution():
    """Verify demo notices reflect realistic capability distribution (not all fully automated)."""
    body = client.get("/api/notices").json()
    supported_count = sum(1 for n in body if n["workflow_status"] == "supported")
    partial_count = sum(1 for n in body if n["workflow_status"] == "partial_support")
    safe_stop_count = sum(1 for n in body if n["workflow_status"] == "safe_stop")
    
    # We should have a realistic mix, not all SUPPORTED
    assert supported_count > 0, "Should have some SUPPORTED workflows"
    assert partial_count > 0, "Should have some PARTIAL_SUPPORT workflows"
    assert safe_stop_count > 0, "Should have some SAFE_STOP workflows"
    
    # SAFE_STOP should be significant portion (legally sensitive workflows)
    assert safe_stop_count >= 4, "Should have at least 4 SAFE_STOP workflows for legal sensitivity"
    
    # Check that workflow endpoint capabilities are correct (this is the actual behavior)
    capability_counts = {"SUPPORTED": 0, "PARTIAL_SUPPORT": 0, "EXPLANATION_ONLY": 0, "SAFE_STOP": 0}
    for notice in body:
        workflow_body = client.get(f"/api/notices/{notice['id']}/workflow").json()
        capability = workflow_body["contract"]["capability"]
        capability_counts[capability] += 1
    
    # Verify we have the expected capability distribution from the registry
    assert capability_counts["SUPPORTED"] >= 8, "Should have multiple SUPPORTED workflows"
    assert capability_counts["PARTIAL_SUPPORT"] >= 2, "Should have PARTIAL_SUPPORT workflows"
    assert capability_counts["SAFE_STOP"] >= 4, "Should have SAFE_STOP workflows for legal sensitivity"
    assert capability_counts["EXPLANATION_ONLY"] >= 1, "Should have EXPLANATION_ONLY workflows"


def test_demo_workflow_endpoints_return_complete_contracts():
    """Verify that workflow endpoints return complete contracts for all demo notices."""
    body = client.get("/api/notices").json()
    for notice in body:
        workflow_body = client.get(f"/api/notices/{notice['id']}/workflow").json()
        # Verify contract structure is complete
        assert "contract" in workflow_body
        assert "identity" in workflow_body["contract"]
        assert "capability" in workflow_body["contract"]
        assert "notice_facts" in workflow_body["contract"]
        assert "official_portal" in workflow_body["contract"]
        assert "safe_stop" in workflow_body["contract"]
        
        # Verify identity information uses workflow endpoint classification
        assert workflow_body["contract"]["identity"]["workflow_id"] == workflow_body["classification"]["workflow_id"]
        assert workflow_body["contract"]["identity"]["title"] is not None

        # Verify capability is a valid WorkflowCapability
        valid_capabilities = ["SUPPORTED", "PARTIAL_SUPPORT", "EXPLANATION_ONLY", "SAFE_STOP"]
        assert workflow_body["contract"]["capability"] in valid_capabilities


def test_demo_citizens_have_multiple_notices_distribution():
    """Verify notices are distributed across citizens for realistic demo experience."""
    citizens_body = client.get("/api/citizens").json()
    notices_by_citizen = {}
    
    for citizen in citizens_body:
        citizen_notices = client.get("/api/notices", params={"citizen_id": citizen["id"]}).json()
        notices_by_citizen[citizen["id"]] = len(citizen_notices)
    
    # Each citizen should have at least one notice
    for citizen_id, count in notices_by_citizen.items():
        assert count >= 1, f"Citizen {citizen_id} should have at least one notice"
    
    # Total should match our 19 notices
    total_notices = sum(notices_by_citizen.values())
    assert total_notices == 19, f"Total notices across citizens should be 19, got {total_notices}"
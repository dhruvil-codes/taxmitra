"""Regression tests for full-PDF extraction followed by provider classification."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.ai import notice_classifier
from app.config import Settings
from app.routers import notices as notices_router
from tests.test_pdf_extraction import REAL_NOTICE_SHAPE, pdf_with_text


client = TestClient(app)


def test_real_notice_shape_routes_when_section_reference_is_missing(monkeypatch):
    # This mirrors the real notice shape that previously stopped at the
    # section-regex gate. OCR/layout loss can remove the section heading while
    # leaving the department identity, annexure language, and requests intact.
    text = REAL_NOTICE_SHAPE.replace("under section 142(1)", "issued under the Income-tax Act")
    seen: dict = {}

    def fake_classifier(notice, settings):
        seen.update(notice)
        return ({
            "is_income_tax_communication": True,
            "category": "scrutiny_142_1",
            "section": "142(1)",
            "confidence": 0.96,
            "reason": "Income Tax Department sender and a scrutiny information schedule are present.",
            "evidence": [
                {"kind": "department_identity", "value": "Income Tax Department", "page_number": 1},
                {"kind": "request_structure", "value": "furnish accounts or documents or information", "page_number": 1},
            ],
        }, None)

    monkeypatch.setattr(notices_router, "classify_notice_with_ai", fake_classifier)
    response = client.post("/api/workflows/extract", files={"file": ("real-notice.pdf", pdf_with_text(text), "application/pdf")})

    assert response.status_code == 200
    body = response.json()
    assert seen["pages"]
    assert seen["official_text"]
    assert body["metadata"]["section"] == "142(1)"
    assert body["classification"]["category"] == "scrutiny_142_1"
    assert body["classification"]["evidence"]
    assert body["workflow"]["workflow_id"] == "scrutiny_142_1"
    assert body["workflow"]["frontend_entry"] == "scrutiny"
    assert len(body["requests"]) == 21


def test_non_income_document_is_rejected_after_extraction(monkeypatch):
    def fake_classifier(notice, settings):
        return ({
            "is_income_tax_communication": False,
            "category": "unknown_income_tax_communication",
            "confidence": 0.99,
            "reason": "The extracted document is a bank statement, not a department communication.",
            "evidence": [{"kind": "document_identity", "value": "bank statement", "page_number": 1}],
        }, None)

    monkeypatch.setattr(notices_router, "classify_notice_with_ai", fake_classifier)
    response = client.post(
        "/api/workflows/extract",
        files={"file": ("not-tax.pdf", pdf_with_text("Bank statement\nAccount activity\nOpening balance 10,000"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["classification"]["category"] == "unknown_income_tax_communication"
    assert body["classification"]["status"] == "safe_stop"
    assert body["workflow"]["capability"] == "SAFE_STOP"
    assert body["extraction"]["refusal_reason"] is None


def test_ai_explanation_only_route_does_not_become_unsupported_section(monkeypatch):
    def fake_classifier(notice, settings):
        return ({
            "is_income_tax_communication": True,
            "category": "scrutiny_information_133_6",
            "section": "133(6)",
            "confidence": 0.94,
            "reason": "The communication asks for information under section 133(6).",
            "evidence": [{"kind": "request_language", "value": "furnish information", "page_number": 1}],
        }, None)

    monkeypatch.setattr(notices_router, "classify_notice_with_ai", fake_classifier)
    response = client.post(
        "/api/workflows/extract",
        files={"file": ("1336.pdf", pdf_with_text("Income Tax Department\nPlease furnish information and documents requested by the Assessing Officer."), "application/pdf")},
    )

    body = response.json()
    assert body["classification"]["category"] == "scrutiny_information_133_6"
    assert body["classification"]["capability"] == "EXPLANATION_ONLY"
    assert body["classification"]["status"] == "explanation_only"
    assert body["workflow"]["capability"] == "EXPLANATION_ONLY"


def test_openai_adapter_receives_all_extracted_pages(monkeypatch):
    seen: dict[str, str] = {}

    class FakeProvider:
        def __init__(self, settings):
            assert settings.openai_api_key == "test-key"

        def chat_json(self, system, user):
            seen["system"] = system
            seen["user"] = user
            return {"is_income_tax_communication": True, "category": "unknown_income_tax_communication", "confidence": 0.4}

    monkeypatch.setattr(notice_classifier, "ChatProvider", FakeProvider)
    proposal, warning = notice_classifier.classify_notice_with_ai(
        {"pages": [
            {"page_number": 1, "source": "text", "confidence": 0.9, "text": "Income Tax Department heading"},
            {"page_number": 2, "source": "ocr", "confidence": 0.7, "text": "Annexure and response deadline"},
        ]},
        Settings(openai_api_key="test-key", demo_mode=False),
    )

    assert warning is None
    assert proposal and "PAGE 1" in seen["user"] and "PAGE 2" in seen["user"]
    assert "Annexure and response deadline" in seen["user"]

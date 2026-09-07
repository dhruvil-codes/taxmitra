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
    assert body["workflow"]["frontend_entry"] == "journey"
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


def test_ai_133_6_route_becomes_supported_information_workflow(monkeypatch):
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
    assert body["classification"]["capability"] == "SUPPORTED"
    assert body["classification"]["status"] == "supported"
    assert body["workflow"]["capability"] == "SUPPORTED"


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


def test_scanned_notice_with_ocr_noise_identified_as_income_tax(monkeypatch):
    """Verify that a genuine scanned Income Tax notice with OCR artifacts is recognized

    and not misclassified or dropped to 'Other proceedings'.
    """
    scanned_noisy_text = """
    1NCOME TAX DEPARTMENT
    GOVERNMENT OF INDlA
    Natlonal Faceless Assessment Centre
    PAN: ABCDE1234F | A.Y. 2024-25 | DIN: ITBA/AST/S/142(1)/2024-25/1068832811(1)
    NOTICE UNDER SECTlON 142(1) OF THE INCOME TAX ACT, 1961
    Sir/Madam,
    In connection with assessment for A.Y. 2024-25, you are requested to produce:
    1. Books of account and cash book.
    2. Bank statements of all accounts maintained during F.Y. 2023-24.
    3. Computation of total income.
    Response Due Date: 15/10/2024
    """
    response = client.post(
        "/api/workflows/extract",
        files={"file": ("scanned_notice.pdf", pdf_with_text(scanned_noisy_text), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["classification"]["category"] == "scrutiny_142_1"
    assert body["classification"]["workflow_id"] == "scrutiny_142_1"
    assert body["workflow"]["capability"] == "SUPPORTED"
    assert body["metadata"]["section"] == "142(1)"
    assert len(body["requests"]) >= 1
    # Verify no 'Other proceedings' fallback in title or classification
    assert "other proceedings" not in str(body).lower()


def test_unsupported_proceeding_scanned_safe_stops_with_explicit_reason():
    """Verify that an income tax communication for an unsupported proceeding (e.g. 148 reassessment)

    stops cleanly with explicit classification, not generic other proceedings.
    """
    reassessment_text = """
    INCOME TAX DEPARTMENT
    GOVERNMENT OF INDIA
    PAN: ABCDE1234F | A.Y. 2021-22
    NOTICE UNDER SECTION 148 OF THE INCOME-TAX ACT, 1961
    I have reason to believe that income chargeable to tax has escaped assessment.
    """
    response = client.post(
        "/api/workflows/extract",
        files={"file": ("notice148.pdf", pdf_with_text(reassessment_text), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is False
    assert body["status"] == "safe_stop"
    assert body["classification"]["category"] == "reassessment_148"
    assert body["classification"]["status"] == "safe_stop"
    assert body["workflow"]["capability"] == "SAFE_STOP"
    assert "legally sensitive" in body["classification"]["reason"].lower() or "reassessment" in body["classification"]["reason"].lower() or "section 148" in body["classification"]["reason"].lower()


def test_illegible_scan_produces_explicit_safe_stop(monkeypatch):
    """Verify that an unreadable or low confidence scan produces an explicit refusal / safe stop."""
    from app.extraction.pdf import PdfExtraction
    def fake_extract(content, grounder=None):
        return PdfExtraction(
            metadata={},
            requests=(),
            text="",
            extraction_confidence=0.1,
            grounding_confidence=0.0,
            grounding_method="none",
            grounding_below_floor=True,
            warnings=("Low OCR quality",),
            refusal_reason="low_extraction_confidence",
            status="refused",
            extraction_method="ocr",
            pages=(),
            page_count=1,
            original_pdf_sha256="abc",
            error_code="low_extraction_confidence",
        )
    monkeypatch.setattr(notices_router, "extract_pdf", fake_extract)
    response = client.post(
        "/api/workflows/extract",
        files={"file": ("illegible.pdf", pdf_with_text("xyz"), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is False
    assert body["status"] == "safe_stop"
    assert body["extraction"]["refusal_reason"] in ("low_extraction_confidence", "ocr_failure")


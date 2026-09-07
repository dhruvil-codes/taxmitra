"""Tests for authentic reply letter generation and export endpoints (PDF, TXT, MD)."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_formal_reply_letter_generated_on_resolve():
    response = client.post(
        "/api/workflow/resolve",
        json={
            "notice_id": "N-2026-003",
            "answers": {
                "cash_deposit_source": "business_income",
                "significant_transaction_explanation": {
                    "choice": "business_transactions",
                    "other": "",
                },
                "other_request_details": "No additional request information",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is True
    draft = data["draft"]

    # Verify authentic Income Tax letterhead & sections
    assert "To" in draft
    assert "Assessment Unit" in draft
    assert "Income Tax Department" in draft
    assert "Ref:" in draft
    assert "ASSESSMENT YEAR:" in draft
    assert "Sub: Reply in accordance with Notice under Section 142(1)" in draft
    assert "Dear Sir/Madam," in draft
    assert "In response to the questionnaire as per the Notice" in draft
    assert "Computation of total income" in draft
    assert "Balance sheet" in draft
    assert "Annexure" in draft
    assert "Thanking you," in draft
    assert "Yours faithfully," in draft
    assert "Tax Mitra has not verified taxpayer facts" in draft


def test_export_endpoint_pdf():
    response = client.post(
        "/api/workflow/export",
        json={
            "text": "Date: 15/10/2026\nTo\nAssessment Unit\nIncome Tax Department\n\nDear Sir/Madam,\nSub: Reply to notice\n\nYours faithfully,\nTaxpayer",
            "format": "pdf",
            "filename": "Reply_Letter",
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=\"Reply_Letter.pdf\"" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_export_endpoint_txt():
    text = "Date: 15/10/2026\nTo Income Tax Department\nTest reply letter"
    response = client.post(
        "/api/workflow/export",
        json={"text": text, "format": "txt", "filename": "Reply_Letter"},
    )
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "attachment; filename=\"Reply_Letter.txt\"" in response.headers["content-disposition"]
    assert response.text == text


def test_export_endpoint_md():
    text = "# Income Tax Reply\n\n**To:** Assessment Unit\n"
    response = client.post(
        "/api/workflow/export",
        json={"text": text, "format": "md", "filename": "Reply_Letter"},
    )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert "attachment; filename=\"Reply_Letter.md\"" in response.headers["content-disposition"]
    assert response.text == text


def test_export_endpoint_invalid_format():
    response = client.post(
        "/api/workflow/export",
        json={"text": "Hello", "format": "docx", "filename": "Reply_Letter"},
    )
    assert response.status_code == 400
    assert "Unsupported export format" in response.json()["detail"]

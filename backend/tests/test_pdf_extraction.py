from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def pdf_with_text(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 10 Tf 40 760 Td ({escaped}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    result = b"%PDF-1.4\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(result)
    result += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode()
    result += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    result += f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return result


NOTICE = """Office of the Assessing Officer
Notice under section 142(1) of the Income-tax Act, 1961 for Assessment Year 2024-25
DIN: DEMO-142-ABC123 Date of issue: 21/08/2026
Please furnish information on or before 18/09/2026.
Annexure A:
1. Detailed computation of total income for Assessment Year 2024-25.
2. Balance sheet as at 31/03/2024.
3. Complete bank statements for all business accounts during FY 2023-24.
"""

REAL_NOTICE_SHAPE = """Income Tax Department
Notice under section 142(1) of the Income-tax Act, 1961 for Assessment Year 2018-19
Reference: ITBA/AST/F/142/2023/1056743063
Please furnish the following accounts or documents or information:
1. Detailed note on all business activities and financial sources.
2. Detailed computation of income.
3. Comparative complete balance sheet and P&L.
4. Complete statements of all bank accounts and transactions.
5. Month-wise cash deposits.
6. Documentary evidence for sources of cash deposits.
7. Date-wise ledger of cash withdrawals.
8. SCRIPTS-wise profit and loss for shares and equities.
9. Name and address of all brokers.
10. Ledger of share transactions.
11. Details of short term and long term capital gain.
12. Copy of cash book.
13. Copy of cash flow statement.
14. Sale and purchase deeds for property transactions and capital gain calculation.
15. Detailed computation of capital gain on sale of properties.
16. Details of entities from whom unsecured loan was received.
17. Names and PAN of entities with financial transactions above the threshold.
18. Statement of loan transactions and agreements.
19. Ledger of all investments and source of funds.
20. Detailed depreciation chart of fixed assets.
21. Put to use certificate for fixed assets.
"""


def test_text_pdf_extracts_metadata_requests_and_grounding():
    response = client.post("/api/scrutiny/extract", files={"file": ("notice.pdf", pdf_with_text(NOTICE), "application/pdf")})
    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["extraction"]["status"] == "needs_confirmation"
    assert body["metadata"]["section"] == "142(1)"
    assert body["metadata"]["assessment_year"] == "2024-25"
    assert body["metadata"]["response_deadline"] == "2026-09-18"
    assert len(body["requests"]) == 3
    assert body["requests"][0]["request_id"].startswith("req-")
    assert body["requests"][0]["grounding"]["method"] == "lexical"


def test_real_notice_shape_accepts_supported_authority_only_requests_without_lowering_floor():
    response = client.post("/api/scrutiny/extract", files={"file": ("notice.pdf", pdf_with_text(REAL_NOTICE_SHAPE), "application/pdf")})
    body = response.json()
    assert body["supported"] is True
    assert body["extraction"]["status"] == "needs_confirmation"
    assert len(body["requests"]) == 21
    capital = next(item for item in body["requests"] if "capital gain on sale" in item["original_text"])
    assert capital["classification_id"] == "req_notice_document"
    assert capital["grounding"]["below_floor"] is False
    assert capital["citations"]
    assert capital["citations"][0]["verification_status"] == "VERIFIED_OFFICIAL"


def test_intentionally_unsupported_request_is_refused():
    text = NOTICE.replace("1. Detailed computation of total income for Assessment Year 2024-25.", "1. Provide a horoscope and astrology prediction for the taxpayer.")
    body = client.post("/api/scrutiny/extract", files={"file": ("notice.pdf", pdf_with_text(text), "application/pdf")}).json()
    assert body["supported"] is False
    assert body["extraction"]["refusal_reason"] == "unsupported_request"


def test_confirmation_fingerprint_is_required_and_unlocks_dynamic_questions():
    extracted = client.post("/api/scrutiny/extract", files={"file": ("notice.pdf", pdf_with_text(NOTICE), "application/pdf")}).json()
    extraction_id = extracted["extraction_id"]
    assert client.get(f"/api/scrutiny/{extraction_id}/questions").status_code == 409
    bad = client.post("/api/scrutiny/confirm", json={"extraction_id": extraction_id, "fingerprint": "bad", "confirmed": True})
    assert bad.status_code == 409
    confirmed = client.post("/api/scrutiny/confirm", json={"extraction_id": extraction_id, "fingerprint": extracted["fingerprint"], "confirmed": True})
    assert confirmed.status_code == 200
    assert confirmed.json()["notice_id"] == extraction_id
    questions = client.get(f"/api/scrutiny/{extraction_id}/questions").json()
    assert len(questions["questions"]) == 3
    answers = {question["id"]: "yes" for question in questions["questions"]}
    resolved = client.post("/api/scrutiny/resolve", json={"notice_id": extraction_id, "answers": answers})
    assert resolved.status_code == 200
    assert resolved.json()["supported"] is True
    assert "Tax Mitra has not submitted" in resolved.json()["official_step"]["boundary"]["en"]


def test_confirmation_accepts_corrections_before_downstream_questions():
    extracted = client.post("/api/scrutiny/extract", files={"file": ("notice.pdf", pdf_with_text(NOTICE), "application/pdf")}).json()
    request_id = extracted["requests"][0]["request_id"]
    corrected = "Corrected original request wording from the taxpayer review."
    response = client.post("/api/scrutiny/confirm", json={
        "extraction_id": extracted["extraction_id"],
        "fingerprint": extracted["fingerprint"],
        "confirmed": True,
        "corrections": {request_id: corrected},
    })
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    assert response.json()["requests"][0]["original_text"] == corrected


def test_scanned_empty_malformed_and_unsupported_files_refuse():
    empty = client.post("/api/scrutiny/extract", files={"file": ("notice.pdf", b"", "application/pdf")}).json()
    assert empty["supported"] is False and empty["extraction"]["refusal_reason"] == "empty_pdf"
    scanned = client.post("/api/scrutiny/extract", files={"file": ("scan.pdf", pdf_with_text("image"), "application/pdf")}).json()
    assert scanned["supported"] is False and scanned["extraction"]["refusal_reason"] == "ocr_not_supported"
    malformed = client.post("/api/scrutiny/extract", files={"file": ("bad.pdf", b"not a pdf", "application/pdf")}).json()
    assert malformed["supported"] is False and malformed["extraction"]["refusal_reason"] == "malformed_pdf"
    unsupported = client.post("/api/scrutiny/extract", files={"file": ("other.pdf", pdf_with_text(NOTICE.replace("142(1)", "148")), "application/pdf")}).json()
    assert unsupported["supported"] is False


def test_file_type_and_size_validation():
    assert client.post("/api/scrutiny/extract", files={"file": ("x.txt", b"hello", "text/plain")}).status_code == 415
    response = client.post("/api/scrutiny/extract", files={"file": ("big.pdf", b"x" * (10 * 1024 * 1024 + 1), "application/pdf")})
    assert response.status_code == 200
    assert response.json()["extraction"]["refusal_reason"] == "file_too_large"

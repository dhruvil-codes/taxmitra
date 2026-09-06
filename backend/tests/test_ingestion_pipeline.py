"""Contract tests for the PDF -> reviewable notice ingestion boundary."""
from __future__ import annotations

from app.ingestion.ocr import OcrResult
from app.ingestion.pipeline import _numbered_requests, ingest_pdf
from app.ingestion.validation import validate_pdf
from tests.test_pdf_extraction import NOTICE, pdf_with_text
from pypdf import PdfReader, PdfWriter


def pdf_with_pages(*texts: str) -> bytes:
    writer = PdfWriter()
    for text in texts:
        writer.add_page(PdfReader(__import__("io").BytesIO(pdf_with_text(text))).pages[0])
    output = __import__("io").BytesIO()
    writer.write(output)
    return output.getvalue()


class FakeOcr:
    def extract(self, content: bytes, page_count: int) -> OcrResult:
        return OcrResult(({
            "page_number": 1,
            "text": NOTICE,
            "source": "ocr",
        },), "needs_confirmation", "OCR output requires review.")


class MixedOcr:
    def extract_pages(self, content: bytes, page_numbers: tuple[int, ...]) -> OcrResult:
        return OcrResult(tuple({
            "page_number": page_number,
            "text": "Section 142(1)\n2. Scanned annexure request for source documents and ₹45,000 dated 18/09/2026.",
            "source": "ocr",
            "confidence": 0.58,
        } for page_number in page_numbers), "needs_confirmation", "OCR was used for scanned pages.")


class PoorOcr:
    def extract_pages(self, content: bytes, page_numbers: tuple[int, ...]) -> OcrResult:
        return OcrResult(tuple({"page_number": page_number, "text": "??", "source": "ocr", "confidence": 0.25} for page_number in page_numbers), "needs_confirmation", "OCR text is too poor to trust.")


def test_text_pdf_is_extracted_with_metadata_and_page_provenance():
    result = ingest_pdf(pdf_with_text(NOTICE), "notice.pdf", "application/pdf")
    assert result.status == "needs_confirmation"
    assert result.supported is True
    assert result.extraction_method == "text"
    assert result.metadata["section"] == "142(1)"
    assert result.requests[0]["original_text"].startswith("Detailed computation")
    assert result.requests[0]["page_number"] == 1
    assert result.requests[0]["source_location"] == "page 1"


def test_scanned_pdf_uses_ocr_but_remains_untrusted():
    result = ingest_pdf(pdf_with_text("image"), "scan.pdf", "application/pdf", FakeOcr())
    assert result.extraction_method == "ocr"
    assert result.status == "needs_confirmation"
    assert result.confidence < 0.7
    assert any("OCR" in warning for warning in result.warnings)


def test_invalid_empty_and_password_protected_inputs_are_deterministic():
    assert validate_pdf(b"", "empty.pdf", "application/pdf").code == "empty_pdf"
    assert validate_pdf(b"not pdf", "bad.pdf", "application/pdf").code == "invalid_pdf"
    assert validate_pdf(b"hello", "bad.txt", "text/plain").code == "invalid_file_type"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("secret")
    import io
    encrypted = io.BytesIO()
    writer.write(encrypted)
    assert validate_pdf(encrypted.getvalue(), "locked.pdf", "application/pdf").code == "password_protected_pdf"


def test_multi_page_requests_keep_their_source_page():
    page_one = NOTICE.replace("2. Balance", "")
    page_two = "2. Balance sheet as at 31/03/2024."
    result = ingest_pdf(pdf_with_pages(page_one, page_two), "notice.pdf", "application/pdf")
    assert result.requests
    assert result.requests[0]["page_number"] == 1
    assert result.requests[-1]["page_number"] == 2


def test_mixed_pdf_ocr_is_limited_to_weak_pages_and_keeps_page_order():
    page_one = NOTICE
    page_two = "scan"
    result = ingest_pdf(pdf_with_pages(page_one, page_two), "mixed.pdf", "application/pdf", MixedOcr())

    assert result.extraction_method == "mixed"
    assert [page["page_number"] for page in result.pages] == [1, 2]
    assert result.pages[0]["source"] == "text"
    assert result.pages[1]["source"] == "ocr"
    assert result.pages[1]["confidence"] < 0.7
    assert any(request["page_number"] == 2 for request in result.requests)


def test_page_text_preserves_tables_amounts_dates_sections_and_long_content():
    table = """Notice under section 139(9)\nAnnexure A\n1. Correct the defect shown in the return.\nParticulars | Amount (INR) | Date\nTax credit | INR 45,000 | 18/09/2026\n"""
    long_text = table + "\n".join(f"Clause {index}: Preserve this complete clause." for index in range(1, 80))
    result = ingest_pdf(pdf_with_pages(long_text, "2. Second page clause with section 154 and ₹12,500."), "long.pdf", "application/pdf", MixedOcr())

    assert result.pages[0]["text"].find("INR 45,000") >= 0
    assert "18/09/2026" in result.pages[0]["text"]
    assert "Clause 79" in result.pages[0]["text"]
    assert result.pages[1]["page_number"] == 2


def test_poor_ocr_is_exposed_as_low_confidence_and_bilingual_text_keeps_order():
    poor = ingest_pdf(pdf_with_text("scan"), "poor.pdf", "application/pdf", PoorOcr())
    assert poor.confidence < 0.7
    assert any("poor" in warning.lower() for warning in poor.warnings)

    requests = _numbered_requests((
        {"page_number": 1, "text": "1. Computation of Total Income / कुल आय की computation", "source": "text"},
        {"page_number": 2, "text": "2. Balance Sheet / बैलेंस शीट", "source": "text"},
    ))
    assert [item["page_number"] for item in requests] == [1, 2]
    assert "कुल आय" in requests[0]["original_text"]


def test_annexure_wording_is_not_replaced_by_a_paraphrase():
    result = ingest_pdf(pdf_with_text(NOTICE), "notice.pdf", "application/pdf")
    original = result.requests[0]["original_text"]
    assert original == "Detailed computation of total income for Assessment Year 2024-25."
    assert "In simple terms" not in original


def test_nested_clauses_bullets_and_multiline_requests_keep_full_source_wording():
    pages = ({"page_number": 3, "text": "1(a). Provide the Balance Sheet\ncontinued with schedules and liabilities.\n1(b) Provide the Profit and Loss Account.\n• Furnish bank statements for the relevant year.\n", "source": "text"},)
    requests = _numbered_requests(pages)
    assert len(requests) == 3
    assert "continued with schedules" in requests[0]["original_text"]
    assert "1(a)." in requests[0]["source_text"]
    assert all(item["page_number"] == 3 for item in requests)


def test_unnumbered_request_is_marked_for_confirmation():
    requests = _numbered_requests(({"page_number": 4, "text": "Please provide the source of cash deposits and supporting documents.", "source": "text"},))
    assert len(requests) == 1
    assert requests[0]["confidence"] <= 0.65
    assert requests[0]["warnings"]

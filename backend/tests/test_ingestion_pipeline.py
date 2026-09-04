"""Contract tests for the PDF -> reviewable notice ingestion boundary."""
from __future__ import annotations

from app.ingestion.ocr import OcrResult
from app.ingestion.pipeline import ingest_pdf
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


def test_annexure_wording_is_not_replaced_by_a_paraphrase():
    result = ingest_pdf(pdf_with_text(NOTICE), "notice.pdf", "application/pdf")
    original = result.requests[0]["original_text"]
    assert original == "Detailed computation of total income for Assessment Year 2024-25."
    assert "In simple terms" not in original

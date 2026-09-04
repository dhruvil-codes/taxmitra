"""Optional OCR adapter. OCR output is always marked unconfirmed."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrResult:
    pages: tuple[dict, ...]
    status: str
    warning: str | None = None


class OcrProvider:
    """Adapter boundary so OCR never leaks into UI or rules code."""

    def extract(self, content: bytes, page_count: int) -> OcrResult:
        try:
            import fitz  # type: ignore
            import pytesseract  # type: ignore
            from PIL import Image  # noqa: F401
        except ImportError:
            return OcrResult((), "unavailable", "This appears to be a scanned PDF, but OCR is not available on this server.")

        try:
            document = fitz.open(stream=content, filetype="pdf")
            pages = []
            for index, page in enumerate(document):
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                text = pytesseract.image_to_string(image).strip()
                pages.append({"page_number": index + 1, "text": text, "source": "ocr"})
            if not any(page["text"] for page in pages):
                return OcrResult(tuple(pages), "failed", "OCR did not identify readable text in this PDF.")
            return OcrResult(tuple(pages), "needs_confirmation", "OCR was used. Check every extracted field against the original PDF.")
        except Exception:
            return OcrResult((), "failed", "OCR could not read this PDF reliably.")


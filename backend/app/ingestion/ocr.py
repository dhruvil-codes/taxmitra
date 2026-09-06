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
        return self.extract_pages(content, tuple(range(1, page_count + 1)))

    def extract_pages(self, content: bytes, page_numbers: tuple[int, ...]) -> OcrResult:
        try:
            import fitz  # type: ignore
            import pytesseract  # type: ignore
            from pytesseract import Output  # type: ignore
            from PIL import Image
        except ImportError:
            return OcrResult((), "unavailable", "This appears to be a scanned PDF, but OCR is not available on this server.")

        try:
            document = fitz.open(stream=content, filetype="pdf")
            pages = []
            for page_number in page_numbers:
                if page_number < 1 or page_number > len(document):
                    continue
                page = document[page_number - 1]
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                languages = set(pytesseract.get_languages(config=""))
                lang = "eng+hin" if {"eng", "hin"}.issubset(languages) else "eng"
                text = pytesseract.image_to_string(image, lang=lang, config="--psm 6").strip()
                data = pytesseract.image_to_data(image, lang=lang, config="--psm 6", output_type=Output.DICT)
                scores = [float(value) for value, word in zip(data.get("conf", []), data.get("text", [])) if word.strip() and float(value) >= 0]
                confidence = round(max(0.25, min(0.78, (sum(scores) / len(scores) / 100) if scores else 0.25)), 3)
                pages.append({"page_number": page_number, "text": text, "source": "ocr", "confidence": confidence})
            document.close()
            if not any(page["text"] for page in pages):
                return OcrResult(tuple(pages), "failed", "OCR did not identify readable text in this PDF.")
            return OcrResult(tuple(pages), "needs_confirmation", "OCR was used. Check every extracted field against the original PDF.")
        except Exception:
            return OcrResult((), "failed", "OCR could not read this PDF reliably.")

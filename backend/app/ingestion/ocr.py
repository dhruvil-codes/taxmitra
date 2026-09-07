"""Optional OCR adapter. OCR output is always marked unconfirmed."""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_rapid_ocr_engine = None


def _get_rapid_ocr():
    global _rapid_ocr_engine
    if _rapid_ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapid_ocr_engine = RapidOCR()
        except Exception as err:
            logger.warning("RapidOCR engine could not be initialized: %s", err)
            _rapid_ocr_engine = False
    return _rapid_ocr_engine if _rapid_ocr_engine is not False else None


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
            import pymupdf as fitz  # type: ignore
            from PIL import Image
        except ImportError:
            try:
                import fitz  # type: ignore
                from PIL import Image
            except ImportError:
                return OcrResult((), "unavailable", "This appears to be a scanned PDF, but PDF rendering is not available on this server.")

        rapid_engine = _get_rapid_ocr()

        try:
            document = fitz.open(stream=content, filetype="pdf")
            pages = []
            for page_number in page_numbers:
                if page_number < 1 or page_number > len(document):
                    continue
                page = document[page_number - 1]

                # First check if PyMuPDF can directly extract clean text from this page
                native_text = (page.get_text() or "").strip()

                text = ""
                confidence = 0.58

                # If RapidOCR is available, render page pixmap and run OCR
                if rapid_engine is not None:
                    try:
                        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                        ocr_res, _ = rapid_engine(image)
                        if ocr_res:
                            lines = [item[1].strip() for item in ocr_res if item[1] and item[1].strip()]
                            scores = [float(item[2]) for item in ocr_res if len(item) > 2]
                            text = "\n".join(lines).strip()
                            avg_score = (sum(scores) / len(scores)) if scores else 0.65
                            confidence = round(max(0.35, min(0.85, avg_score)), 3)
                    except Exception as err:
                        logger.warning("RapidOCR failed on page %d: %s", page_number, err)

                # Fallback to pytesseract if RapidOCR yielded no text or was unavailable
                if not text:
                    try:
                        import pytesseract  # type: ignore
                        from pytesseract import Output  # type: ignore
                        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                        languages = set(pytesseract.get_languages(config=""))
                        lang = "eng+hin" if {"eng", "hin"}.issubset(languages) else "eng"
                        text = pytesseract.image_to_string(image, lang=lang, config="--psm 6").strip()
                        data = pytesseract.image_to_data(image, lang=lang, config="--psm 6", output_type=Output.DICT)
                        scores = [float(value) for value, word in zip(data.get("conf", []), data.get("text", [])) if word.strip() and float(value) >= 0]
                        confidence = round(max(0.25, min(0.78, (sum(scores) / len(scores) / 100) if scores else 0.25)), 3)
                    except Exception:
                        pass

                # If OCR didn't find text, but native text exists on the page, use native text
                if not text and native_text:
                    text = native_text
                    confidence = 0.85

                pages.append({"page_number": page_number, "text": text, "source": "ocr" if text != native_text else "text", "confidence": confidence})

            document.close()
            if not any(page["text"] for page in pages):
                return OcrResult(tuple(pages), "failed", "OCR did not identify readable text in this PDF.")
            return OcrResult(tuple(pages), "needs_confirmation", "OCR was used. Check every extracted field against the original PDF.")
        except Exception as e:
            logger.error("OCR extraction exception: %s", e)
            return OcrResult((), "failed", "OCR could not read this PDF reliably.")


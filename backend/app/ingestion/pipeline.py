"""Validate, extract, assess reliability, OCR if needed, and structure notices."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date

from app.ingestion.ocr import OcrProvider
from app.ingestion.validation import MAX_PDF_BYTES, validate_pdf


@dataclass(frozen=True)
class IngestionResult:
    metadata: dict
    requests: tuple[dict, ...]
    pages: tuple[dict, ...]
    status: str
    supported: bool
    confidence: float
    warnings: tuple[str, ...]
    refusal_reason: str | None
    page_count: int
    original_pdf_sha256: str
    extraction_method: str


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\r\n-–—")


def _date(value: str) -> str | None:
    try:
        day, month, year = (int(part) for part in re.split(r"[/\-]", value))
        return date(year + (2000 if year < 100 else 0), month, day).isoformat()
    except (ValueError, TypeError):
        return None


def _metadata(text: str) -> dict:
    ref = re.search(r"\b(?:DIN|reference|ref(?:erence)?\s*(?:no|number)?)[\s:#-]*([A-Z0-9][A-Z0-9./_-]{5,})", text, re.I)
    ay = re.search(r"(?:assessment\s+year|AY)\s*[:\-]?\s*((?:20)\d{2}\s*[-–]\s*\d{2})", text, re.I)
    deadline = re.search(r"(?:on or before|due date|respond by|deadline)\D{0,35}(\d{1,2}[/-]\d{1,2}[/-](?:20)?\d{2})", text, re.I)
    issue = re.search(r"(?:date of issue|issued on|notice date)\D{0,20}(\d{1,2}[/-]\d{1,2}[/-](?:20)?\d{2})", text, re.I)
    authority = re.search(r"(?:office of the|issued by|from)\s+([^\n]{3,100})", text, re.I)
    return {
        "notice_reference": ref.group(1) if ref else None,
        "section": re.search(r"section\s*142\s*[\(\[]\s*1\s*[\)\]]", text, re.I) and "142(1)" or None,
        "assessment_year": re.sub(r"\s", "", ay.group(1)).replace("–", "-") if ay else None,
        "response_deadline": _date(deadline.group(1)) if deadline else None,
        "issue_date": _date(issue.group(1)) if issue else None,
        "issuing_authority": _clean(authority.group(1)) if authority else None,
        "taxpayer_identifier": None,
    }


def _numbered_requests(pages: tuple[dict, ...]) -> list[dict]:
    found: list[dict] = []
    for page in pages:
        lines = [_clean(line) for line in page["text"].splitlines()]
        starts = [i for i, line in enumerate(lines) if re.match(r"^(?:\(?\d{1,2}\)?[.)]|Q(?:uestion)?\s*\d{1,2}[.:)])\s+", line, re.I)]
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(lines)
            value = _clean(" ".join(lines[start:end]))
            value = re.sub(r"^(?:\(?\d{1,2}\)?[.)]|Q(?:uestion)?\s*\d{1,2}[.:)])\s+", "", value, flags=re.I)
            value = re.sub(r"\s+(?:Pending|Status|Response\s+status)\s*$", "", value, flags=re.I)
            for stop in ("submit the response", "assessing officer", "signature and office"):
                if stop in value.lower():
                    value = value[:value.lower().index(stop)].strip()
            if len(value) >= 15:
                found.append({"original_text": value, "page_number": page["page_number"], "source_location": f"page {page['page_number']}"})
    return found


def ingest_pdf(content: bytes, filename: str | None, content_type: str | None, ocr_provider: OcrProvider | None = None) -> IngestionResult:
    fingerprint = hashlib.sha256(content).hexdigest()
    validation = validate_pdf(content, filename, content_type)
    if not validation.ok:
        return IngestionResult({}, (), (), "uploaded", False, 0.0, (validation.message or "The PDF could not be processed.",), validation.code, 0, fingerprint, "none")

    pages = tuple({"page_number": i + 1, "text": (page.extract_text() or "").strip(), "source": "text"} for i, page in enumerate(validation.reader.pages))
    text_chars = sum(len(page["text"]) for page in pages)
    text_pages = sum(bool(page["text"]) for page in pages)
    reliable = text_chars >= 80 and text_pages >= max(1, len(pages) // 2)
    method = "text"
    warnings: list[str] = []
    if not reliable:
        ocr = (ocr_provider or OcrProvider()).extract(content, len(pages))
        if ocr.status == "needs_confirmation":
            pages = ocr.pages
            method = "ocr"
            warnings.append(ocr.warning or "OCR output requires confirmation.")
        else:
            return IngestionResult({}, (), pages, "needs_confirmation", False, 0.0, (ocr.warning or "The PDF text could not be extracted reliably.",), "ocr_failure" if ocr.status == "failed" else "low_extraction_confidence", len(pages), fingerprint, "ocr")
    full_text = "\n".join(page["text"] for page in pages)
    metadata = _metadata(full_text)
    if not metadata["section"]:
        return IngestionResult(metadata, (), pages, "unsupported", False, 0.0, tuple(warnings) + ("Tax Mitra currently supports Section 142(1) scrutiny notices in this workflow.",), "unsupported_notice", len(pages), fingerprint, method)
    requests = _numbered_requests(pages)
    if not requests:
        return IngestionResult(metadata, (), pages, "needs_confirmation", False, 0.0, tuple(warnings) + ("No clearly numbered annexure or questionnaire requests were found.",), "missing_critical_information", len(pages), fingerprint, method)
    confidence = 0.88 if method == "text" else 0.58
    if method == "ocr":
        warnings.append("OCR text is not authoritative. Compare the original wording, dates, identifiers, and page numbers before confirming.")
    return IngestionResult(metadata, tuple({**item, "request_id": "req-" + hashlib.sha256(item["original_text"].encode()).hexdigest()[:16], "confidence": confidence, "warnings": list(warnings)} for item in requests), pages, "needs_confirmation", True, confidence, tuple(dict.fromkeys(warnings)), None, len(pages), fingerprint, method)


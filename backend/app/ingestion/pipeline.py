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
        textual = re.fullmatch(r"\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*", value)
        if textual:
            month = {name.lower(): index for index, name in enumerate(("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"), 1)}.get(textual.group(2).lower())
            if month:
                return date(int(textual.group(3)), month, int(textual.group(1))).isoformat()
        day, month, year = (int(part) for part in re.split(r"[/\-]", value))
        return date(year + (2000 if year < 100 else 0), month, day).isoformat()
    except (ValueError, TypeError):
        return None


def _metadata(text: str) -> dict:
    ref = re.search(r"\b(?:DIN|reference|ref(?:erence)?\s*(?:no|number)?)[\s:#-]*([A-Z0-9][A-Z0-9./_-]{5,})", text, re.I)
    ay = re.search(r"(?:assessment\s+year|AY)\s*[:\-]?\s*((?:20)\d{2}\s*[-–]\s*\d{2})", text, re.I)
    deadline = re.search(r"(?:on or before|due date|respond by|deadline)\D{0,35}(\d{1,2}(?:[/-]\d{1,2}[/-](?:20)?\d{2}|\s+[A-Za-z]+\s+\d{4}))", text, re.I)
    issue = re.search(r"(?:date of issue|issued on|notice date)\D{0,20}(\d{1,2}(?:[/-]\d{1,2}[/-](?:20)?\d{2}|\s+[A-Za-z]+\s+\d{4}))", text, re.I)
    authority = re.search(r"(?:office of the|issued by|from)\s+([^\n]{3,100})", text, re.I)
    return {
        "notice_reference": ref.group(1) if ref else None,
        "section": _section(text),
        "assessment_year": re.sub(r"\s", "", ay.group(1)).replace("–", "-") if ay else None,
        "response_deadline": _date(deadline.group(1)) if deadline else None,
        "issue_date": _date(issue.group(1)) if issue else None,
        "issuing_authority": _clean(authority.group(1)) if authority else None,
        "taxpayer_identifier": None,
}


def _section(text: str) -> str | None:
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?|\b)\s*143\s*[\(\[]\s*1\s*[\)\]]\s*[\(\[]\s*a\s*[\)\]]", text, re.I):
        return "143(1)(a)"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?|\b)\s*142\s*[\(\[]\s*1\s*[\)\]]", text, re.I) or re.search(r"\b142\(1\)\b", text, re.I) or re.search(r"ITBA/AST/[A-Z]/142\b", text, re.I):
        return "142(1)"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?|\b)\s*139\s*[\(\[]\s*9\s*[\)\]]", text, re.I):
        return "139(9)"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?|\b)\s*133\s*[\(\[]\s*6\s*[\)\]]", text, re.I):
        return "133(6)"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?|\b)\s*148\s*[\(\[]\s*a\s*[\)\]]", text, re.I) or re.search(r"(?:section|sec\.?|s\.?|u/s\.?)\s*148a\b", text, re.I):
        return "148A"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?)\s*148\b", text, re.I) or re.search(r"\bnotice\s+under\s+section\s+148\b", text, re.I):
        return "148"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?)\s*245\b", text, re.I) or "adjustment against demand" in text.lower():
        return "245"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?)\s*154\b", text, re.I) or re.search(r"\bmistake\s+apparent\b", text, re.I):
        return "154"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?|\b)\s*143\s*[\(\[]\s*1\s*[\)\]]", text, re.I):
        return "143(1)"
    if re.search(r"(?:section|sec\.?|s\.?|u/s\.?|\b)\s*131\b", text, re.I) and any(term in text.lower() for term in ("summons", "attendance")):
        return "131"
    return None


def _numbered_requests(pages: tuple[dict, ...]) -> list[dict]:
    found: list[dict] = []
    for page in pages:
        lines = [_clean(line) for line in page["text"].splitlines()]
        marker = r"(?:\(?\d{1,3}\)?[.)]|\d{1,3}(?:\([a-z]\)|\([ivx]+\))+(?:[.:)])?|Q(?:uestion)?\s*\d{1,3}[.:)]|[•●▪◦]\s+|(?<!\w)[-–—]\s+)"
        starts = [i for i, line in enumerate(lines) if re.match(rf"^{marker}\s*\S", line, re.I)]
        inferred = False
        if not starts:
            # Unnumbered requests are accepted only when a line has clear
            # request language and a tax-document term. They remain lower
            # confidence and require human confirmation.
            request_terms = r"computation|balance sheet|profit and loss|bank statement|ledger|annexure|challan|tax credit|cash deposit|supporting document|information"
            request_verbs = r"provide|furnish|submit|explain|clarification|requested|required|details of"
            starts = [i for i, line in enumerate(lines) if len(line) >= 20 and re.search(request_terms, line, re.I) and re.search(request_verbs, line, re.I)]
            inferred = bool(starts)
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(lines)
            value = _clean(" ".join(lines[start:end]))
            source_text = value
            value = re.sub(rf"^{marker}\s*", "", value, flags=re.I)
            value = re.sub(r"\s+(?:Pending|Status|Response\s+status)\s*$", "", value, flags=re.I)
            if len(value) >= 15:
                found.append({
                    "original_text": value,
                    "source_text": source_text,
                    "page_number": page["page_number"],
                    "source_location": f"page {page['page_number']}",
                    "confidence": min(page.get("confidence", 0.88 if page.get("source") == "text" else 0.58), 0.65) if inferred else page.get("confidence", 0.88 if page.get("source") == "text" else 0.58),
                    "warnings": ["Request boundary inferred from unnumbered notice text; confirm against the original page."] if inferred else [],
                })
    return found


def _has_embedded_image(page: object) -> bool:
    """Detect image-backed pages without requiring a text layer."""
    try:
        return bool(getattr(page, "images"))
    except (AttributeError, TypeError, ValueError):
        return False


def ingest_pdf(content: bytes, filename: str | None, content_type: str | None, ocr_provider: OcrProvider | None = None) -> IngestionResult:
    fingerprint = hashlib.sha256(content).hexdigest()
    validation = validate_pdf(content, filename, content_type)
    if not validation.ok:
        return IngestionResult({}, (), (), "uploaded", False, 0.0, (validation.message or "The PDF could not be processed.",), validation.code, 0, fingerprint, "none")

    source_pages = tuple(validation.reader.pages)
    pages = tuple({"page_number": i + 1, "text": (page.extract_text() or ""), "source": "text", "confidence": 0.88} for i, page in enumerate(source_pages))
    # Short pages can still be perfectly usable (for example a one-line
    # continuation or a numbered annexure item). Only OCR genuinely sparse
    # pages; this is the mixed-PDF fast path.
    image_pages = {i + 1 for i, page in enumerate(source_pages) if _has_embedded_image(page)}
    weak_pages = tuple(
        page["page_number"]
        for page in pages
        if len(page["text"].strip()) < 20 or page["page_number"] in image_pages
    )
    method = "text"
    warnings: list[str] = []
    if weak_pages:
        provider = ocr_provider or OcrProvider()
        ocr = provider.extract_pages(content, weak_pages) if hasattr(provider, "extract_pages") else provider.extract(content, len(pages))
        ocr_by_page = {page["page_number"]: page for page in ocr.pages}
        merged = []
        for page in pages:
            if page["page_number"] in weak_pages and page["page_number"] in ocr_by_page and ocr_by_page[page["page_number"]].get("text", "").strip():
                ocr_page = ocr_by_page[page["page_number"]]
                native_text = page["text"].strip()
                ocr_text = ocr_page.get("text", "").strip()
                combined = "\n".join(value for value in (native_text, ocr_text) if value)
                merged.append({**page, "text": combined, "source": "ocr" if len(native_text) < 20 else "mixed", "confidence": min(page.get("confidence", 0.88), ocr_page.get("confidence", 0.58))})
            else:
                merged.append(page)
        pages = tuple(merged)
        method = "ocr" if len(weak_pages) == len(pages) else "mixed"
        warnings.append(ocr.warning or "OCR output requires confirmation for one or more pages.")
        if ocr.status in {"failed", "unavailable"}:
            return IngestionResult({}, (), pages, "needs_confirmation", False, 0.0, tuple(warnings), "ocr_failure" if ocr.status == "failed" else "low_extraction_confidence", len(pages), fingerprint, method)
        if any(not page["text"].strip() for page in pages if page["page_number"] in weak_pages):
            warnings.append("One or more pages remain unreadable after OCR. Review the original PDF before continuing.")
    full_text = "\n".join(page["text"] for page in pages)
    metadata = _metadata(full_text)
    meaningful_characters = len(re.sub(r"\W", "", full_text, flags=re.UNICODE))
    if meaningful_characters < 20:
        return IngestionResult(metadata, (), pages, "needs_confirmation", False, 0.0, tuple(warnings) + ("The extracted pages do not contain enough readable text for classification.",), "low_extraction_confidence", len(pages), fingerprint, method)
    if not metadata["section"]:
        warnings.append("No section reference was confidently extracted; communication classification will use the full notice language and structure.")
    requests = _numbered_requests(pages)
    if not requests:
        # 143(1)(a) is a mismatch/intimation workflow; it does not have the
        # numbered annexure request schedule required by scrutiny 142(1).
        # Keep extraction usable so the universal classifier can route it to
        # the existing Journey flow.
        if metadata["section"] == "143(1)(a)":
            confidence = round(sum(page.get("confidence", 0.88) for page in pages) / len(pages), 3) if pages else 0.0
            return IngestionResult(metadata, (), pages, "needs_confirmation", True, confidence, tuple(warnings), None, len(pages), fingerprint, method)
        confidence = round(sum(page.get("confidence", 0.88) for page in pages) / len(pages), 3) if pages else 0.0
        return IngestionResult(metadata, (), pages, "needs_confirmation", True, confidence, tuple(warnings) + ("No clearly numbered annexure or questionnaire requests were found; classification will use the communication as a whole.",), None, len(pages), fingerprint, method)
    confidence = round(sum(page.get("confidence", 0.88) for page in pages) / len(pages), 3) if pages else 0.0
    if method in {"ocr", "mixed"}:
        warnings.append("OCR text is not authoritative. Compare the original wording, dates, identifiers, and page numbers before confirming.")
    return IngestionResult(metadata, tuple({**item, "request_id": "req-" + hashlib.sha256(item["original_text"].encode()).hexdigest()[:16], "confidence": confidence, "warnings": list(warnings)} for item in requests), pages, "needs_confirmation", True, confidence, tuple(dict.fromkeys(warnings)), None, len(pages), fingerprint, method)

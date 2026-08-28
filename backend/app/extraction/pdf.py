"""Conservative, text-only PDF extraction for Section 142(1) notices."""
from __future__ import annotations

import hashlib
import io
import logging
import re
from dataclasses import dataclass
from datetime import date

from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 10 * 1024 * 1024

@dataclass(frozen=True)
class PdfExtraction:
    metadata: dict
    requests: tuple[dict, ...]
    text: str
    extraction_confidence: float
    grounding_confidence: float
    grounding_method: str
    grounding_below_floor: bool
    warnings: tuple[str, ...]
    refusal_reason: str | None = None

def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\r\n-–—")

def _parse_date(value: str) -> str | None:
    parts = re.split(r"[/\-]", value)
    if len(parts) != 3:
        return None
    try:
        day, month, year = (int(p) for p in parts)
        year += 2000 if year < 100 else 0
        return date(year, month, day).isoformat()
    except ValueError:
        return None

def _metadata(text: str) -> dict:
    ref = re.search(r"\b(?:DIN|reference|ref(?:erence)?\s*(?:no|number)?)[\s:#-]*([A-Z0-9][A-Z0-9./_-]{5,})", text, re.I)
    ay = re.search(r"(?:assessment\s+year|AY)\s*[:\-]?\s*((?:20)\d{2}\s*[-–]\s*\d{2})", text, re.I)
    deadline = re.search(r"(?:on or before|due date|respond by|deadline)\D{0,35}(\d{1,2}[/-]\d{1,2}[/-](?:20)?\d{2})", text, re.I)
    issue = re.search(r"(?:date of issue|issued on|notice date)\D{0,20}(\d{1,2}[/-]\d{1,2}[/-](?:20)?\d{2})", text, re.I)
    return {
        "notice_reference": ref.group(1) if ref else None,
        "section": "142(1)" if re.search(r"section\s*142\s*[\(\[]\s*1\s*[\)\]]", text, re.I) else None,
        "assessment_year": re.sub(r"\s", "", ay.group(1)).replace("–", "-") if ay else None,
        "response_deadline": _parse_date(deadline.group(1)) if deadline else None,
        "issue_date": _parse_date(issue.group(1)) if issue else None,
    }

def _items(text: str) -> list[str]:
    lines = [_clean(line) for line in text.splitlines()]
    starts = [i for i, line in enumerate(lines) if re.match(r"^(?:\(?\d{1,2}\)?[.)]|Q(?:uestion)?\s*\d{1,2}[.:)])\s+", line, re.I)]
    out = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        value = _clean(" ".join(lines[start:end]))
        value = re.sub(r"^(?:\(?\d{1,2}\)?[.)]|Q(?:uestion)?\s*\d{1,2}[.:)])\s+", "", value, flags=re.I)
        if len(value) >= 15:
            out.append(value)
    return out

def _classify(item: str):
    value = item.lower()
    # These requests need topic-specific law that is not present in the
    # current 1961 corpus. Preserve the exact notice wording and ground only
    # the authority to request information under section 142(1).
    if any(needle in value for needle in ("capital gain", "capital loss", "property transaction", "share", "equity", "scrip", "broker", "cash withdrawal", "cash withdrawn", "cash book", "cash flow", "unsecured loan", "financial transaction", "investment", "depreciation", "fixed asset", "loan transaction", "business activities", "financial sources")):
        return "req_notice_document", f"Request: {item}", ("sec-142-0001",)
    rules = (
        (("computation", "total income", "income computation"), "req_computation_income", "Computation of total income", ("kb-142-1-scrutiny-documents",)),
        (("balance sheet",), "req_balance_sheet", "Balance sheet", ("kb-142-1-scrutiny-documents",)),
        (("profit and loss", "profit & loss", "p&l account"), "req_profit_loss", "Profit and Loss account", ("kb-142-1-scrutiny-documents",)),
        (("bank statement", "bank account"), "req_bank_statements", "Bank statements", ("kb-142-1-scrutiny-documents",)),
        (("cash deposit",), "req_cash_deposits", "Sources of cash deposits", ("kb-142-1-written-information",)),
        (("significant credit", "significant debit", "credits and debits"), "req_significant_transactions", "Significant credits and debits", ("kb-142-1-written-information",)),
    )
    for needles, kind, section, citations in rules:
        if any(needle in value for needle in needles):
            return kind, section, citations
    return None

def _is_heading(item: str) -> bool:
    value = item.lower()
    return "following accounts or documents or information" in value or ("142(1)" in value and "furnish" not in value)

def extract_pdf(content: bytes, ground_query) -> PdfExtraction:
    if not content:
        return PdfExtraction({}, (), "", 0, 0, "lexical", True, ("The PDF is empty.",), "empty_pdf")
    if len(content) > MAX_PDF_BYTES:
        return PdfExtraction({}, (), "", 0, 0, "lexical", True, ("The PDF exceeds the 10 MB limit.",), "file_too_large")
    try:
        reader = PdfReader(io.BytesIO(content), strict=False)
        page_count = len(reader.pages)
        text = "\n".join("\n".join(_clean(line) for line in (page.extract_text() or "").splitlines()) for page in reader.pages)
        logger.info(f"PyPDF EXTRACTION: pages={page_count}, text_length={len(text)}, is_empty={len(text.strip()) == 0}")
        if len(text) > 0:
            preview = text[:200].replace('\n', ' ') if len(text) > 200 else text.replace('\n', ' ')
            logger.info(f"TEXT PREVIEW: {preview}")
    except Exception:
        return PdfExtraction({}, (), "", 0, 0, "lexical", True, ("The PDF could not be read safely.",), "malformed_pdf")
    text = text.strip()
    if len(text) < 80:
        return PdfExtraction({}, (), text, 0, 0, "lexical", True, ("OCR is not supported in V1; this PDF has no reliably extractable text.",), "ocr_not_supported")
    metadata = _metadata(text)
    if metadata["section"] != "142(1)":
        return PdfExtraction(metadata, (), text, 0, 0, "lexical", True, ("Only Section 142(1) scrutiny notices are supported in V1.",), "unsupported_notice")
    items = _items(text)
    logger.info(f"DETECTED NUMBERED ITEMS: count={len(items)}")
    # Log retrieval method before processing items
    import os
    vectors_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "vectors.json")
    vectors_exists = os.path.exists(vectors_path)
    logger.info(f"RETRIEVAL SETUP: vectors.json_exists={vectors_exists}, path={vectors_path}")
    extracted, scores, warnings = [], [], []
    for idx, item in enumerate(items):
        truncated = item[:100] if len(item) > 100 else item
        logger.info(f"ITEM[{idx}]: {truncated}")
        classified = _classify(item)
        if not classified:
            logger.info(f"CLASSIFICATION[{idx}]: UNCLASSIFIED - item_truncated={item[:50]}")
            if _is_heading(item):
                continue
            warnings.append("One numbered item could not be classified safely.")
            return PdfExtraction(metadata, (), text, 0, 0, "lexical", True, tuple(warnings), "unsupported_request")
        kind, response_section, citations = classified
        logger.info(f"CLASSIFICATION[{idx}]: SUCCESS - kind={kind}, response_section={response_section}")
        result = ground_query("section 142(1) accounts documents verified written information " + item)
        logger.info(f"GROUNDING[{idx}]: method={result.method}, confidence={result.confidence:.3f}, below_floor={result.below_floor}")
        scores.append(result.confidence)
        authoritative = [chunk.id for chunk in result.chunks if chunk.verification_status == "VERIFIED_OFFICIAL" and chunk.status == "CURRENT"]
        if not authoritative:
            authoritative = list(citations)
        extracted.append({
            "request_id": "req-" + hashlib.sha256(item.encode("utf-8")).hexdigest()[:16],
            "classification_id": kind,
            "original_text": item,
            "response_section": response_section,
            "citations": authoritative,
            "grounding": {"method": result.method, "confidence": round(result.confidence, 3), "below_floor": result.below_floor},
            "confidence": round(min(0.98, 0.72 + (0.20 if result.confidence >= 0.25 else 0)), 3),
            "warnings": ["Grounding is below the confidence floor; confirm this item carefully."] if result.below_floor else [],
        })
    logger.info(f"CLASSIFICATION COMPLETE: classified_items={len(extracted)}, total_items={len(items)}")
    if not extracted:
        reason = "no_supported_requests"
        if len(items) == 0:
            reason = "no_supported_requests_no_items_detected"
        elif len(warnings) > 0:
            reason = f"no_supported_requests_classification_failed: {warnings[0]}"
        else:
            reason = "no_supported_requests_empty_extraction"
        logger.error(f"NO_SUPPORTED_REQUESTS: detected_items={len(items)}, classified_items={len(extracted)}, reason={reason}")
        return PdfExtraction(metadata, (), text, 0, 0, "lexical", True, tuple(warnings) or ("No supported numbered scrutiny requests were found.",), "no_supported_requests")
    grounding = min(scores)
    warnings = list(dict.fromkeys(warnings))
    if grounding < 0.25:
        warnings.append("Grounding is below the safe floor for at least one request.")
        return PdfExtraction(metadata, tuple(extracted), text, 0, round(grounding, 3), "lexical", True, tuple(warnings), "grounding_below_floor")
    confidence = min(0.98, 0.70 + (0.15 if metadata["assessment_year"] else 0) + (0.10 if metadata["response_deadline"] else 0))
    return PdfExtraction(metadata, tuple(extracted), text, round(confidence, 3), round(grounding, 3), "lexical", grounding < 0.25, tuple(warnings))

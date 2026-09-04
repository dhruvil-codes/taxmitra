"""Conservative, text-only PDF extraction for Section 142(1) notices."""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import date

from app.ingestion.pipeline import ingest_pdf

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
    status: str = "needs_confirmation"
    extraction_method: str = "text"
    pages: tuple[dict, ...] = ()
    page_count: int = 0
    original_pdf_sha256: str | None = None
    error_code: str | None = None

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
    
    # Detect both formats: "1. Text" and "1" followed by "Text"
    # Format 1: Number and text on same line
    same_line_starts = [i for i, line in enumerate(lines) if re.match(r"^(?:\(?\d{1,2}\)?[.)]|Q(?:uestion)?\s*\d{1,2}[.:)])\s+", line, re.I)]
    
    # Format 2: Number on separate line (e.g., "1" then "Text")
    multi_line_starts = []
    for i, line in enumerate(lines):
        if re.match(r"^\d{1,2}\s*$", line.strip()) and i + 1 < len(lines):
            # Check if next line looks like item text (not another number)
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if len(next_line) >= 10 and not re.match(r"^\d{1,2}\s*$", next_line.strip()):
                multi_line_starts.append(i)
    
    # Combine both detection methods
    all_starts = sorted(set(same_line_starts + multi_line_starts))
    
    out = []
    for pos, start in enumerate(all_starts):
        end = all_starts[pos + 1] if pos + 1 < len(all_starts) else len(lines)
        value = _clean(" ".join(lines[start:end]))
        # Remove numbering from same-line format
        value = re.sub(r"^(?:\(?\d{1,2}\)?[.)]|Q(?:uestion)?\s*\d{1,2}[.:)])\s+", "", value, flags=re.I)
        # Remove standalone number from multi-line format
        value = re.sub(r"^\d{1,2}\s+", "", value, flags=re.I)
        # Remove "Pending" and similar status words that might be captured
        value = re.sub(r"\s+(?:Pending|Status|Response\s+status)\s*$", "", value, flags=re.I)
        # Remove trailing status words anywhere in the string
        value = re.sub(r"\s+pending\s*", "", value, flags=re.I)
        # Stop at footer-like content - more aggressive cleanup
        for stop_phrase in ["submit the response", "assessing officer", "prescribed income-tax", "signature and office", "income tax department"]:
            if stop_phrase in value.lower():
                value = value.lower().split(stop_phrase)[0].strip()
                break
        # Final cleanup of any remaining trailing junk
        value = re.sub(r"\s+", " ", value).strip()
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
        # Additional rules for demo PDF items
        (("ledger extract", "supporting invoices", "professional receipts"), "req_ledger_extract", "Ledger extract and supporting invoices", ("kb-142-1-scrutiny-documents",)),
        (("high-value transactions", "ais", "sft"), "req_high_value_transactions", "Explanation of high-value transactions", ("kb-142-1-written-information",)),
        (("tax payments", "tds", "tcs", "challan"), "req_tax_payments", "Details of tax payments and challans", ("kb-142-1-scrutiny-documents",)),
        (("deduction", "exemption", "80c", "80d"), "req_deductions_exemptions", "Supporting documents for deductions and exemptions", ("kb-142-1-scrutiny-documents",)),
        (("evidence", "support of the return"), "req_evidence", "Supporting evidence for the return", ("kb-142-1-scrutiny-documents",)),
    )
    for needles, kind, section, citations in rules:
        if any(needle in value for needle in needles):
            return kind, section, citations
    return None

def _is_heading(item: str) -> bool:
    value = item.lower()
    return "following accounts or documents or information" in value or ("142(1)" in value and "furnish" not in value)

def extract_pdf(content: bytes, ground_query) -> PdfExtraction:
    result = ingest_pdf(content, "notice.pdf", "application/pdf")
    text = "\n".join(page.get("text", "") for page in result.pages).strip()
    # Keep legacy refusal identifiers stable for existing clients while the
    # explicit error_code/status fields expose the new deterministic states.
    refusal = result.refusal_reason
    if refusal == "invalid_pdf":
        refusal = "malformed_pdf"
    if refusal == "ocr_failure":
        refusal = "ocr_not_supported"
    if result.refusal_reason and result.refusal_reason not in {"unsupported_notice", "missing_critical_information"}:
        return PdfExtraction(result.metadata, (), text, result.confidence, 0, "lexical", False, result.warnings, refusal, result.status, result.extraction_method, result.pages, result.page_count, result.original_pdf_sha256, result.refusal_reason)
    if result.refusal_reason == "unsupported_notice":
        return PdfExtraction(result.metadata, (), text, 0, 0, "not_run", True, result.warnings, "unsupported_notice", "unsupported", result.extraction_method, result.pages, result.page_count, result.original_pdf_sha256, result.refusal_reason)
    metadata = result.metadata
    items = [(item["original_text"], item["page_number"]) for item in result.requests]
    logger.info(f"DETECTED NUMBERED ITEMS: count={len(items)}")
    extracted, scores, warnings = [], [], []
    for idx, (item, page_number) in enumerate(items):
        truncated = item[:100] if len(item) > 100 else item
        logger.info(f"ITEM[{idx}]: {truncated}")
        classified = _classify(item)
        if not classified:
            logger.info(f"CLASSIFICATION[{idx}]: UNCLASSIFIED - item_truncated={item[:50]}")
            if _is_heading(item):
                continue
            warnings.append("One numbered item could not be classified safely.")
            return PdfExtraction(metadata, (), text, 0, 0, "not_run", True, tuple(warnings), "unsupported_request", "unsupported", result.extraction_method, result.pages, result.page_count, result.original_pdf_sha256, "unsupported_request")
        kind, response_section, citations = classified
        logger.info(f"CLASSIFICATION[{idx}]: SUCCESS - kind={kind}, response_section={response_section}")
        # Retrieval is intentionally deferred until confirmation. These are
        # classification citations only, not evidence that the request is safe.
        scores.append(0.0)
        authoritative = list(citations)
        extracted.append({
            "request_id": "req-" + hashlib.sha256(item.encode("utf-8")).hexdigest()[:16],
            "classification_id": kind,
            "original_text": item,
            "response_section": response_section,
            "citations": authoritative,
            "page_number": page_number,
            "source_location": f"page {page_number}",
            "grounding": {"method": "lexical", "confidence": 0.0, "below_floor": False},
            "confidence": round(result.confidence, 3),
            "warnings": ["Retrieval and guidance are intentionally deferred until confirmation."],
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
        return PdfExtraction(metadata, (), text, 0, 0, "not_run", True, tuple(warnings) or ("No supported numbered scrutiny requests were found.",), "no_supported_requests", "unsupported", result.extraction_method, result.pages, result.page_count, result.original_pdf_sha256, "no_supported_requests")
    grounding = 0.0
    warnings = list(dict.fromkeys(warnings))
    confidence = result.confidence
    return PdfExtraction(metadata, tuple(extracted), text, round(confidence, 3), grounding, "lexical", False, tuple(dict.fromkeys(warnings + list(result.warnings))), None, "needs_confirmation", result.extraction_method, result.pages, result.page_count, result.original_pdf_sha256)

"""Notice document extraction boundary.

Production PDF/OCR work belongs behind this module. The rules engine consumes
only confirmed structured requests, so replacing the synthetic extractor later
does not require rewriting the scrutiny workflow.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedRequest:
    id: str
    original_text: str
    response_section: str
    citations: tuple[str, ...]
    classification_id: str | None = None
    confidence: float = 1.0
    warnings: tuple[str, ...] = ()
    grounding: dict | None = None
    page_number: int | None = None
    source_location: str | None = None
    category: str | None = None
    required_evidence: tuple[dict, ...] = ()
    clarifying_questions: tuple[dict, ...] = ()
    status: str = "not_started"
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExtractedNotice:
    notice_id: str
    source_type: str
    requires_human_confirmation: bool
    requests: tuple[ExtractedRequest, ...]


def extract_notice_requests(notice: dict) -> ExtractedNotice:
    """Extract structured annexure requests from a notice-like document.

    V1/demo uses deterministic synthetic extraction data already attached to
    the synthetic notice. Real PDF parsing/OCR can later populate the same
    object shape and still require human confirmation before rules run.
    """
    extraction = notice.get("synthetic_extraction") or {}
    requests = tuple(
        ExtractedRequest(
            id=str(item.get("id", item.get("request_id", ""))),
            original_text=str(item["original_text"]),
            response_section=str(item["response_section"]),
            citations=tuple(str(cid) for cid in item.get("citations", ())),
            classification_id=item.get("classification_id"),
            confidence=float(item.get("confidence", 1.0)),
            warnings=tuple(str(w) for w in item.get("warnings", ())),
            grounding=item.get("grounding"),
            page_number=item.get("page_number", item.get("page")),
            source_location=item.get("source_location") or (f"page {item.get('page_number', item.get('page'))}" if item.get("page_number", item.get("page")) else None),
            category=str(item["category"]) if item.get("category") else None,
            required_evidence=tuple(item.get("required_evidence", ())),
            clarifying_questions=tuple(item.get("clarifying_questions", ())),
            status=str(item.get("status", "not_started")),
            sources=tuple(str(source) for source in item.get("sources", item.get("citations", ()))),
        )
        for item in extraction.get("requests", ())
    )
    return ExtractedNotice(
        notice_id=str(notice.get("id", "")),
        source_type=str(extraction.get("source_type", "unknown")),
        requires_human_confirmation=bool(extraction.get("requires_human_confirmation", True)),
        requests=requests,
    )


def confirmed_requests(extracted: ExtractedNotice, confirmed: bool) -> tuple[ExtractedRequest, ...]:
    """Return requests only after a human has confirmed the extraction."""
    if extracted.requires_human_confirmation and not confirmed:
        return ()
    return extracted.requests

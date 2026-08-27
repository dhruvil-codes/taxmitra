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
            id=str(item["id"]),
            original_text=str(item["original_text"]),
            response_section=str(item["response_section"]),
            citations=tuple(str(cid) for cid in item.get("citations", ())),
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

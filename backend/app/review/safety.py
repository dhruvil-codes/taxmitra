"""Deterministic pre-response safety checks.

This layer does not decide tax law. It verifies that the workflow has enough
confirmed, grounded input to present a draft for human review.
"""

from __future__ import annotations

import re
from typing import Any


def evaluate(notice: dict, requests: tuple[Any, ...], answers: dict[str, str], evidence: list[dict], draft: str, *, supported: bool, extraction_confirmed: bool, verified_sources: bool) -> dict:
    checks = []

    def add(key: str, label: str, passed: bool, missing: str) -> None:
        checks.append({"key": key, "label": label, "status": "passed" if passed else "blocked", "missing": None if passed else missing})

    add("notice_type", "Supported notice type", supported, "This notice type is not supported by this workflow.")
    add("critical_fields", "Critical notice fields", bool(notice.get("section") and notice.get("assessment_year")), "The notice section or Assessment Year could not be confirmed.")
    add("user_confirmation", "User-confirmed information", extraction_confirmed and bool(requests), "Confirm the extracted notice requests before continuing.")
    expected = {f"evidence_{request.id}" for request in requests}
    add("required_questions", "Required questions answered", expected <= set(answers), "Answer every required question.")
    unresolved = [key for key in expected if answers.get(key) == "unsure"]
    add("unresolved_uncertainty", "No unresolved critical Not sure states", not unresolved, "Verify the items marked Not sure before preparing an actionable response.")
    add("evidence_identified", "Required evidence identified", bool(evidence) and all(item.get("requirement_level") for item in evidence), "No request-specific evidence mapping is available.")
    add("verified_sources", "Important explanations grounded in verified sources", verified_sources, "At least one important explanation does not have a verified source.")
    safe_language = not bool(re.search(r"\b(Tax Mitra|we)\s+(has\s+)?(submitted|filed|sent)\b", draft or "", re.I))
    add("supported_conclusions", "No unsupported legal or tax conclusion", safe_language, "The draft contains a submission or legal conclusion that needs review.")
    add("confirmed_draft", "Draft based on confirmed information", bool(draft and requests and expected <= set(answers)), "The draft is missing or is not linked to the confirmed request answers.")
    add("submission_boundary", "Tax Mitra has not submitted anything", "has not submitted" in (draft or "").lower() or "does not submit" in (draft or "").lower(), "The submission boundary must remain in the draft.")
    blocked = [check for check in checks if check["status"] == "blocked"]
    return {"status": "ready" if not blocked else "blocked", "ready": not blocked, "checks": checks, "missing": [check["missing"] for check in blocked]}

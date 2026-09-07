"""Cached loaders for the synthetic data files."""

from __future__ import annotations

import json
import os
from functools import lru_cache

from app.config import get_settings


@lru_cache(maxsize=1)
def _read(file_name: str) -> list | dict:
    path = os.path.join(get_settings().data_dir, file_name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_citizens() -> list[dict]:
    return _read("citizens.json")


def load_notices() -> list[dict]:
    return _read("notices.json")


def get_notice(notice_id: str) -> dict | None:
    found = next((n for n in load_notices() if n["id"] == notice_id), None)
    if found:
        return found
    from app.extraction.sessions import get_session
    session = get_session(notice_id)
    if not session or not session.get("confirmed"):
        return None
    metadata = session.get("metadata", {})
    stored = dict(session.get("notice") or {})
    return {
        **stored,
        "id": notice_id,
        "section": metadata.get("section") or stored.get("section"),
        "assessment_year": metadata.get("assessment_year") or stored.get("assessment_year") or "2024-25",
        "response_due_date": metadata.get("response_deadline") or stored.get("response_due_date"),
        "issue_date": metadata.get("issue_date") or stored.get("issue_date"),
        "official_reference": metadata.get("notice_reference") or stored.get("official_reference") or notice_id,
        "amount_in_question": stored.get("amount_in_question", 0),
        "income_source": stored.get("income_source", "Uploaded notice"),
        "official_text": stored.get("official_text") or "\n".join(page.get("text", "") for page in session.get("pages", [])),
        "citizen_id": stored.get("citizen_id", "uploaded"),
        "synthetic_extraction": {
            **(stored.get("synthetic_extraction") or {}),
            "source_type": "pdf",
            "requires_human_confirmation": not session.get("confirmed", False),
            "requests": session.get("requests", []),
        },
    }


def get_citizen(citizen_id: str) -> dict | None:
    return next((c for c in load_citizens() if c["id"] == citizen_id), None)


def load_draft_templates() -> dict[str, str]:
    return _read("draft_templates.json")

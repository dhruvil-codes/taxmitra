"""Grounded prompts. The model may only use provided context and must
cite provided source ids — no answering from memory, ever."""

from __future__ import annotations

import json

from app.knowledge.corpus_loader import Chunk
from app.rules.terminology import TERMINOLOGY_GUIDANCE


NOTICE_CLASSIFICATION_SYSTEM = (
    "You classify extracted Indian tax communications for a routing engine. "
    "Use only the supplied extracted PDF text and page evidence. Do not invent "
    "sections, deadlines, facts, or obligations. First decide whether the document "
    "is an Indian Income Tax Department communication. If it is not, return false. "
    "If it is, select exactly one category from the supplied registry. A missing or "
    "poorly OCR'd section number must not prevent classification when department "
    "language, headings, requests, dates, sender, and structure support a category. "
    "If the evidence is insufficient, use unknown_income_tax_communication with low "
    "confidence. Reply with one JSON object only."
)

EXPLAIN_SYSTEM = (
    "You explain Indian income tax notices to ordinary citizens in plain language. "
    "You answer ONLY from the provided context. If the context does not support an "
    "answer, say so instead of guessing. Never state or imply that the taxpayer owes "
    "money unless the context explicitly says so. "
    f"{TERMINOLOGY_GUIDANCE} Reply with a single JSON object."
)

TRANSLATE_SYSTEM = (
    "You are a careful translator into the requested Indian language. Preserve "
    "meaning, tone, and placeholders like {amount} and {assessment_year} exactly. "
    "Reply with a single JSON object."
)


def _context_block(chunks: tuple[Chunk, ...]) -> str:
    parts = []
    for chunk in chunks:
        parts.append(f"[{chunk.id}] ({chunk.section}) {chunk.title}:\n{chunk.text}")
    return "\n\n".join(parts)


def build_explanation_prompt(notice: dict, chunks: tuple[Chunk, ...], locale: str) -> tuple[str, str]:
    language = "English" if locale == "en" else "Hindi (Devanagari script)"
    user = json.dumps(
        {
            "task": "Explain this income tax notice adjustment in plain language.",
            "notice": {
                "section": notice.get("section"),
                "amount_in_question": notice.get("amount_in_question"),
                "assessment_year": notice.get("assessment_year"),
                "income_source": notice.get("income_source"),
                "issue_date": notice.get("issue_date"),
            },
            "output_language": language,
            "required_json_fields": {
                "plain_language": "2-4 sentences, keep placeholders {amount} {assessment_year} {income_source} where the values would appear",
                "what_this_does_not_mean": "one sentence clarifying this is not automatically a tax demand",
                "possible_reasons": "3-5 short plain-language reasons for the mismatch",
                "citations": "array of context ids you actually used",
            },
            "context": _context_block(chunks),
        },
        ensure_ascii=False,
    )
    return EXPLAIN_SYSTEM, user


def build_translate_prompt(fields: dict, locale: str) -> tuple[str, str]:
    language = "Hindi (Devanagari script)"
    user = json.dumps(
        {
            "task": "Translate each field value.",
            "output_language": language,
            "fields": fields,
            "required_json_fields": {key: "translated value" for key in fields},
            "note": "requested locale code: " + locale,
        },
        ensure_ascii=False,
    )
    return TRANSLATE_SYSTEM, user


def build_notice_classification_prompt(notice: dict, workflows: list[dict]) -> tuple[str, str]:
    """Build a grounded classifier prompt from the complete extracted notice."""
    pages = notice.get("pages") or ()
    page_text = "\n\n".join(
        f"--- PAGE {page.get('page_number', '?')} ({page.get('source', 'unknown')}, confidence {page.get('confidence', 'unknown')}) ---\n"
        f"{page.get('text', '')}"
        for page in pages
    )
    if not page_text:
        page_text = str(notice.get("official_text") or "")
    registry = [
        {"category": item["category"], "title": item["title"], "capability": item["capability"], "signals": item["classification_signals"]}
        for item in workflows
    ]
    user = json.dumps(
        {
            "task": "Classify this complete extracted PDF for safe workflow routing.",
            "required_json_fields": {
                "is_income_tax_communication": "boolean",
                "category": "one registry category or unknown_income_tax_communication",
                "section": "section/proceeding as evidenced, or null",
                "act_version": "Income-tax Act, 1961 or Income Tax Act, 2025 only when supported, otherwise null",
                "authority": "sender or authority wording, or null",
                "communication_type": "short description of the communication, or null",
                "purpose": "what the Department is asking or communicating, or null",
                "deadline": "explicit deadline/date if present, otherwise null",
                "confidence": "number from 0 to 1",
                "reason": "short evidence-grounded explanation",
                "evidence": "array of objects with kind, value, page_number when known",
            },
            "registry": registry,
            "extracted_metadata": {key: value for key, value in notice.items() if key not in {"pages", "official_text"}},
            "complete_extracted_text": page_text,
        },
        ensure_ascii=False,
    )
    return NOTICE_CLASSIFICATION_SYSTEM, user

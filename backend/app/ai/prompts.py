"""Grounded prompts. The model may only use provided context and must
cite provided source ids — no answering from memory, ever."""

from __future__ import annotations

import json

from app.knowledge.corpus_loader import Chunk
from app.rules.terminology import TERMINOLOGY_GUIDANCE

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

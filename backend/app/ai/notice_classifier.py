"""OpenAI-backed notice classification adapter.

The registry remains the sole source of workflow capabilities and routing. This
module only asks the existing chat provider to identify a communication from the
complete extracted text, then returns a validated proposal for the registry.
"""
from __future__ import annotations

from typing import Any

from app.ai.provider import ChatProvider
from app.ai.prompts import build_notice_classification_prompt
from app.config import Settings
from app.knowledge.embedder import AIUnavailableError
from app.workflows.registry import list_workflows


def classify_notice_with_ai(notice: dict[str, Any], settings: Settings) -> tuple[dict[str, Any] | None, str | None]:
    """Classify a notice with the configured provider, degrading safely.

    A missing key, demo mode, provider failure, malformed response, or unknown
    category never becomes a guessed workflow. The caller can use the existing
    deterministic registry fallback and preserve safe-stop semantics.
    """
    if settings.demo_mode or not settings.openai_api_key:
        return None, "AI classification is unavailable in the current runtime; deterministic evidence routing was used."
    try:
        system, user = build_notice_classification_prompt(notice, list_workflows())
        result = ChatProvider(settings).chat_json(system, user)
    except AIUnavailableError as exc:
        return None, f"AI classification could not be completed safely: {exc}"
    if not isinstance(result, dict):
        return None, "AI classification returned an invalid result; safe routing was used."
    return result, None

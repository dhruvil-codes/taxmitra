"""OpenAI chat provider. Model name comes from settings — never hardcoded."""

from __future__ import annotations

import json

from openai import OpenAI

from app.config import Settings
from app.knowledge.embedder import AIUnavailableError


class ChatProvider:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if not self._settings.openai_api_key:
            raise AIUnavailableError("OPENAI_API_KEY is not configured")
        if self._client is None:
            self._client = OpenAI(api_key=self._settings.openai_api_key)
        return self._client

    def chat_json(self, system: str, user: str) -> dict:
        """One structured-JSON completion. Raises AIUnavailableError on failure."""
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self._settings.openai_chat_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return json.loads(response.choices[0].message.content or "{}")
        except AIUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001 - surfaced as graceful degradation
            raise AIUnavailableError(f"chat call failed: {exc}") from exc

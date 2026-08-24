"""Embeddings via OpenAI. Model comes from settings — never hardcoded."""

from __future__ import annotations

from openai import OpenAI

from app.config import Settings


class AIUnavailableError(RuntimeError):
    """Raised when a live AI call is impossible (no key, network, quota)."""


class Embedder:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if not self._settings.openai_api_key:
            raise AIUnavailableError("OPENAI_API_KEY is not configured")
        if self._client is None:
            self._client = OpenAI(api_key=self._settings.openai_api_key)
        return self._client

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        try:
            response = client.embeddings.create(
                model=self._settings.openai_embedding_model,
                input=texts,
            )
        except Exception as exc:  # noqa: BLE001 - surfaced as graceful degradation
            raise AIUnavailableError(f"embedding call failed: {exc}") from exc
        return [item.embedding for item in response.data]

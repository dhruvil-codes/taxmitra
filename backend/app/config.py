"""Central configuration. All model names and secrets come from environment
variables with sane defaults - nothing model-related is hardcoded at call sites."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- OpenAI ---
    openai_api_key: str = ""
    # Model selection is configuration, not code. Override with env vars:
    #   OPENAI_CHAT_MODEL=gpt-4o-mini (default)
    #   OPENAI_EMBEDDING_MODEL=text-embedding-3-small (default)
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # --- Runtime modes ---
    # DEMO_MODE=true  -> AI routes serve ONLY pre-generated/static content.
    # Zero live OpenAI calls, zero cost, immune to quota/outage/abuse.
    demo_mode: bool = False

    # Where pre-generated content lives (committed to the repo).
    static_fallbacks_dir: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "static_fallbacks",
    )
    # Knowledge-base artifacts (vectors.json) produced by scripts/build_kb.py.
    kb_dir: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "knowledge",
    )
    data_dir: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "data",
    )

    # --- Retrieval ---
    retrieval_top_k: int = 4
    # Below this cosine-similarity score we refuse instead of guessing.
    retrieval_confidence_floor: float = 0.30
    # Lexical fallback runs when embeddings are unavailable (no vectors.json,
    # no API key, or DEMO_MODE). Its scores are token-coverage, not cosine,
    # so it carries its own floor.
    lexical_confidence_floor: float = 0.25

    # --- Rate limiting for live-AI routes (public-link abuse guard) ---
    ai_rate_limit: str = "10/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()

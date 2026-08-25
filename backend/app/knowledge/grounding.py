"""Grounding service: retrieve corpus context with whichever method is available.

Preference order:
  1. Embedding retrieval — only when vectors.json exists AND a key is
     configured AND we are not in DEMO_MODE (DEMO_MODE must never touch
     the network, embeddings included).
  2. Lexical retrieval — always available, zero network, zero cost.

Both paths enforce the same contract: a RetrievalResult with a method tag
and a below_floor refusal flag. The confidence gate is therefore always
enforceable, never silently skipped.
"""

from __future__ import annotations

from app.config import Settings
from app.knowledge.embedder import AIUnavailableError, Embedder
from app.knowledge.lexical import build_lexical_retriever
from app.knowledge.retriever import Retriever, RetrievalResult


def available_method(settings: Settings) -> str:
    """Which retrieval method ground() would use, without running it."""
    if settings.demo_mode or not settings.openai_api_key:
        return "lexical"
    if Retriever.load(settings) is None:
        return "lexical"
    return "embedding"


def ground(settings: Settings, query: str, top_k: int | None = None) -> RetrievalResult:
    if available_method(settings) == "embedding":
        try:
            retriever = Retriever.load(settings)
            assert retriever is not None  # available_method() checked
            vector = Embedder(settings).embed_texts([query])[0]
            return retriever.retrieve(vector, top_k=top_k)
        except AIUnavailableError:
            pass  # fall through to lexical — grounding degrades, never dies
    return build_lexical_retriever(settings).retrieve(query, top_k=top_k)

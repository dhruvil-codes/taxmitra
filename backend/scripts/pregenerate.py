"""Pre-generate AI content into static fallbacks (dev-time spend only).

Generates grounded explanations for supported categories/locales via the
live API and writes them to app/static_fallbacks/, so production serves
instant, free, unbreakable content. Budget: well under $0.50 total.

    OPENAI_API_KEY=... python -m scripts.pregenerate
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.prompts import build_explanation_prompt  # noqa: E402
from app.ai.provider import ChatProvider  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.data_store import load_notices  # noqa: E402
from app.knowledge.corpus_loader import load_corpus  # noqa: E402
from app.knowledge.embedder import AIUnavailableError, Embedder  # noqa: E402
from app.knowledge.retriever import Retriever  # noqa: E402
from app.rules.notice_types import SUPPORTED_CATEGORIES, classify_notice  # noqa: E402


def main() -> int:
    settings = get_settings()
    retriever = Retriever.load(settings)
    if retriever is None:
        print("Run scripts/build_kb.py first.")
        return 1
    provider = ChatProvider(settings)
    embedder = Embedder(settings)
    corpus = load_corpus(os.path.join(settings.kb_dir, "corpus"))
    corpus_ids = {c.id for c in corpus}

    for notice in load_notices():
        category = classify_notice(notice)
        if category not in SUPPORTED_CATEGORIES:
            continue
        for locale in ("en", "hi"):
            key = f"explanation_{category.value}_{locale}"
            out_path = os.path.join(settings.static_fallbacks_dir, f"{key}.json")
            if os.path.exists(out_path):
                print(f"exists, skipping: {key}")
                continue
            query = f"explain section {notice['section']} income mismatch intimation {notice['income_source']}"
            try:
                vector = embedder.embed_texts([query])[0]
                result = retriever.retrieve(vector)
                if result.below_floor:
                    print(f"low confidence for {key}: {result.confidence:.3f} — skipped")
                    continue
                system, user = build_explanation_prompt(notice, result.chunks, locale)
                content = provider.chat_json(system, user)
            except AIUnavailableError as exc:
                print(f"AI unavailable for {key}: {exc}")
                continue
            content.setdefault("citations", [c.id for c in result.chunks[:4]])
            content["citations"] = [c for c in content["citations"] if c in corpus_ids]
            content.update(
                kind="explanation",
                category=category.value,
                locale=locale,
                generated_at=date.today().isoformat(),
                generator=f"pregenerate.py ({settings.openai_chat_model})",
                retrieval_confidence=round(result.confidence, 3),
                verification="pending",
            )
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(content, fh, ensure_ascii=False, indent=2)
            print(f"wrote {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

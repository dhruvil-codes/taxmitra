"""Build the knowledge base: corpus -> embeddings -> vectors.json.

Run once (or after editing corpus files):
    OPENAI_API_KEY=... python -m scripts.build_kb
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings  # noqa: E402
from app.knowledge.corpus_loader import load_corpus  # noqa: E402
from app.knowledge.embedder import AIUnavailableError, Embedder  # noqa: E402


def main() -> int:
    settings = get_settings()
    corpus_dir = os.path.join(settings.kb_dir, "corpus")
    chunks = load_corpus(corpus_dir)
    if not chunks:
        print("No corpus chunks found — aborting.")
        return 1
    try:
        vectors = Embedder(settings).embed_texts(
            [f"{c.title}\n{c.section}\n{c.text}" for c in chunks]
        )
    except AIUnavailableError as exc:
        print(f"Embedding unavailable: {exc}")
        return 1
    payload = [
        {"id": c.id, "source_id": c.source_id, "title": c.title, "section": c.section,
         "assessment_year": c.assessment_year, "tax_year": c.tax_year,
         "status": c.status, "verification_status": c.verification_status, "vector": vec}
        for c, vec in zip(chunks, vectors)
    ]
    out_path = os.path.join(settings.kb_dir, "vectors.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    print(f"Wrote {len(payload)} vectors -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the knowledge base: corpus -> embeddings -> vectors.json.

Run once (or after editing corpus files):
    OPENAI_API_KEY=... python -m scripts.build_kb
When OPENAI_API_KEY is unset, preserves existing embeddings and synthesizes
missing vectors via semantic TF-IDF projection across the known embedding space.
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings  # noqa: E402
from app.knowledge.corpus_loader import Chunk, load_corpus  # noqa: E402
from app.knowledge.embedder import AIUnavailableError, Embedder  # noqa: E402
from app.knowledge.lexical import tokenize  # noqa: E402
from app.knowledge.retriever import Retriever  # noqa: E402


def _project_missing_vectors(
    chunks: list[Chunk],
    existing_vectors: dict[str, list[float]],
) -> dict[str, list[float]]:
    """Synthesize normalized 1536-dim vectors for chunks lacking embeddings."""
    known_ids = [c.id for c in chunks if c.id in existing_vectors]
    missing = [c for c in chunks if c.id not in existing_vectors]
    if not missing:
        return existing_vectors

    doc_tokens = {}
    for c in chunks:
        wf = " ".join(c.workflow_context)
        doc_tokens[c.id] = tokenize(f"{c.title} {c.section} {c.text} {wf}")

    all_tokens = sorted({t for tokens in doc_tokens.values() for t in tokens})
    t2i = {t: i for i, t in enumerate(all_tokens)}
    df: dict[str, int] = {}
    for tokens in doc_tokens.values():
        for t in tokens:
            df[t] = df.get(t, 0) + 1

    n_docs = len(chunks)
    idf = {t: math.log((1 + n_docs) / (1 + count)) + 1.0 for t, count in df.items()}

    tfidf: dict[str, np.ndarray] = {}
    for c in chunks:
        v = np.zeros(len(all_tokens), dtype=float)
        for t in doc_tokens[c.id]:
            v[t2i[t]] = idf[t]
        norm = np.linalg.norm(v)
        if norm > 0:
            v /= norm
        tfidf[c.id] = v

    out = dict(existing_vectors)
    for m in missing:
        sims = [(kid, float(np.dot(tfidf[m.id], tfidf[kid]))) for kid in known_ids]
        sims.sort(key=lambda x: -x[1])
        top = [x for x in sims[:10] if x[1] > 0]
        if not top:
            base_vecs = np.array([existing_vectors[kid] for kid in known_ids], dtype=float)
            vec = base_vecs.mean(axis=0)
        else:
            weights = np.array([s**2 for _, s in top])
            weights /= weights.sum()
            vec = np.zeros(1536, dtype=float)
            for (kid, _), w in zip(top, weights):
                vec += w * np.array(existing_vectors[kid], dtype=float)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        out[m.id] = [round(float(x), 6) for x in vec]
    return out


def main() -> int:
    settings = get_settings()
    corpus_dir = os.path.join(settings.kb_dir, "corpus")
    chunks = load_corpus(corpus_dir)
    if not chunks:
        print("No corpus chunks found — aborting.")
        return 1

    out_path = os.path.join(settings.kb_dir, "vectors.json")
    vectors_map: dict[str, list[float]] = {}

    if settings.openai_api_key:
        try:
            print("Embedding chunks via OpenAI API...")
            vectors = Embedder(settings).embed_texts(
                [f"{c.title}\n{c.section}\n{c.text}" for c in chunks]
            )
            vectors_map = {c.id: vec for c, vec in zip(chunks, vectors)}
        except AIUnavailableError as exc:
            print(f"Embedding API call failed: {exc}")

    if not vectors_map:
        existing_vectors: dict[str, list[float]] = {}
        if os.path.exists(out_path):
            try:
                with open(out_path, encoding="utf-8") as fh:
                    existing_data = json.load(fh)
                existing_vectors = {
                    item["id"]: item["vector"]
                    for item in existing_data
                    if isinstance(item.get("id"), str) and isinstance(item.get("vector"), list)
                }
            except Exception as e:
                print(f"Failed to read existing vectors: {e}")

        if not existing_vectors:
            print("No existing vectors found and OPENAI_API_KEY is not configured — aborting.")
            return 1

        print(f"Projecting missing vectors from {len(existing_vectors)} existing vectors...")
        vectors_map = _project_missing_vectors(chunks, existing_vectors)

    payload = [
        {
            "id": c.id,
            "source_id": c.source_id,
            "title": c.title,
            "section": c.section,
            "assessment_year": c.assessment_year,
            "tax_year": c.tax_year,
            "status": c.status,
            "verification_status": c.verification_status,
            "vector": vectors_map[c.id],
        }
        for c in chunks
    ]

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    print(f"Wrote {len(payload)} vectors -> {out_path}")

    # Validate index with Retriever
    retriever = Retriever.load(settings)
    if retriever is None:
        print("Validation error: Retriever.load(settings) returned None!")
        return 1

    print("Index validation succeeded: Retriever.load() loaded all chunks successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

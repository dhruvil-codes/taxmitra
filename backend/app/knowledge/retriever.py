"""In-memory cosine retriever with a confidence floor.

Below the floor we refuse to answer rather than guess — this powers the
unsupported-notice honesty path. Vectors are produced by scripts/build_kb.py
and stored in app/knowledge/vectors.json (id, vector, and a text copy so
retrieval works even without the live API at runtime).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np

from app.config import Settings
from app.knowledge.corpus_loader import Chunk, load_corpus


@dataclass(frozen=True)
class RetrievalResult:
    chunks: tuple[Chunk, ...]
    scores: tuple[float, ...]
    confidence: float
    below_floor: bool
    method: str = "embedding"

    @property
    def verified_source_count(self) -> int:
        return sum(1 for chunk in self.chunks if chunk.verification_status == "VERIFIED_OFFICIAL")


class Retriever:
    def __init__(
        self,
        chunks: tuple[Chunk, ...],
        vectors: np.ndarray,
        default_k: int = 4,
        default_floor: float = 0.30,
    ):
        norm = np.linalg.norm(vectors, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        self._matrix = vectors / norm
        self._chunks = chunks
        self._default_k = default_k
        self._default_floor = default_floor

    @classmethod
    def load(cls, settings: Settings) -> "Retriever | None":
        path = os.path.join(settings.kb_dir, "vectors.json")
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        index = {c.id: c for c in load_corpus(os.path.join(settings.kb_dir, "corpus"))}
        chunks = [index[entry["id"]] for entry in payload if entry["id"] in index]
        vectors = np.array([entry["vector"] for entry in payload if entry["id"] in index], dtype=float)
        if not chunks:
            return None
        return cls(tuple(chunks), vectors, settings.retrieval_top_k, settings.retrieval_confidence_floor)

    def retrieve(
        self,
        query_vector: list[float],
        top_k: int | None = None,
        confidence_floor: float | None = None,
        assessment_year: str | None = None,
        tax_year: str | None = None,
    ) -> RetrievalResult:
        k = top_k or self._default_k
        floor = confidence_floor or self._default_floor
        q = np.array(query_vector, dtype=float)
        q = q / (np.linalg.norm(q) or 1.0)
        scores = self._matrix @ q
        ranked = []
        for i, raw_score in enumerate(scores):
            chunk = self._chunks[i]
            score = float(raw_score)
            if chunk.verification_status == "VERIFIED_OFFICIAL":
                score += 0.08
            else:
                score -= 0.08
            if chunk.status in {"SUPERSEDED", "HISTORICAL"}:
                score -= 0.12
            if assessment_year and chunk.assessment_year:
                score += 0.12 if assessment_year in chunk.assessment_year else -0.12
            if tax_year and chunk.tax_year:
                score += 0.12 if tax_year in chunk.tax_year else -0.12
            ranked.append((score, i))
        ranked.sort(key=lambda pair: (-pair[0], pair[1]))
        order = ranked[:k]
        picked = tuple(self._chunks[i] for _, i in order)
        picked_scores = tuple(score for score, _ in order)
        confidence = picked_scores[0] if picked_scores else 0.0
        return RetrievalResult(
            chunks=picked,
            scores=picked_scores,
            confidence=confidence,
            below_floor=confidence < floor,
        )

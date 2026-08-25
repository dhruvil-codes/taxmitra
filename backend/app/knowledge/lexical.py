"""Lexical retriever — grounding without embeddings.

TF-overlap scoring with IDF weighting over the same corpus the embedding
retriever uses. This is the fallback when vectors.json is absent, the API
key is missing, or DEMO_MODE forbids network calls — which means the
confidence gate is ALWAYS enforceable, never skipped for lack of embeddings.

Section references like 143(1)(a) are kept whole as single tokens; they are
the strongest relevance signal in this domain.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

from app.config import Settings
from app.knowledge.corpus_loader import Chunk, load_corpus
from app.knowledge.retriever import RetrievalResult

_SECTION_RE = re.compile(r"\d+\([0-9a-zA-Z]+\)(?:\([0-9a-zA-Z]+\))*")
_TOKEN_RE = re.compile(r"\w{2,}")

# English + Hindi function words. Section tokens are never listed here.
_STOPWORDS = frozenset(
    """
    the a an of to is in and or for on with by this that be are was were it
    as at from your you we our has have had not no do does did what which
    who whom when where why how if then than so such can could should would
    may might will shall must about into over under again further once
    section notice act under explain
    का के की में से को पर है हैं और यह वह था थे कि जो नहीं क्या कब कहाँ
    """.split()
)


def tokenize(text: str) -> set[str]:
    lowered = text.lower()
    tokens = set(_TOKEN_RE.findall(lowered))
    tokens.update(m.lower() for m in _SECTION_RE.findall(lowered))
    return {t for t in tokens if t not in _STOPWORDS and not t.isdigit()}


class LexicalRetriever:
    def __init__(self, chunks: tuple[Chunk, ...], default_k: int = 4, default_floor: float = 0.25):
        self._chunks = chunks
        self._tokens = [tokenize(c.text) for c in chunks]
        self._default_k = default_k
        self._default_floor = default_floor
        n = max(len(chunks), 1)
        df: dict[str, int] = {}
        for bag in self._tokens:
            for token in bag:
                df[token] = df.get(token, 0) + 1
        self._idf = {t: math.log(1 + n / d) for t, d in df.items()}

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        confidence_floor: float | None = None,
    ) -> RetrievalResult:
        k = top_k or self._default_k
        floor = confidence_floor if confidence_floor is not None else self._default_floor
        query_tokens = tokenize(query)
        total_weight = sum(self._idf.get(t, math.log(1 + len(self._chunks))) for t in query_tokens)
        if total_weight <= 0:
            return RetrievalResult(chunks=(), scores=(), confidence=0.0, below_floor=True, method="lexical")

        scored: list[tuple[float, int]] = []
        for i, bag in enumerate(self._tokens):
            matched = sum(self._idf[t] for t in query_tokens if t in bag)
            scored.append((matched / total_weight, i))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))

        top = scored[:k]
        picked = tuple(self._chunks[i] for _, i in top if _ > 0)
        picked_scores = tuple(score for score, _ in top if score > 0)
        confidence = picked_scores[0] if picked_scores else 0.0
        return RetrievalResult(
            chunks=picked,
            scores=picked_scores,
            confidence=confidence,
            below_floor=confidence < floor,
            method="lexical",
        )


@lru_cache(maxsize=4)
def _cached_lexical(corpus_dir: str, top_k: int, floor: float) -> LexicalRetriever:
    return LexicalRetriever(load_corpus(corpus_dir), top_k, floor)


def build_lexical_retriever(settings: Settings) -> LexicalRetriever:
    import os

    corpus_dir = os.path.join(str(settings.kb_dir), "corpus")
    return _cached_lexical(corpus_dir, settings.retrieval_top_k, settings.lexical_confidence_floor)

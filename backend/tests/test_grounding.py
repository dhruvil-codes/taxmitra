"""Grounding must always work and always be honest.

The lexical fallback exists so the confidence gate is enforceable even
without vectors.json or an API key — these tests pin that contract.
"""

import json
import os

import numpy as np

from app.config import get_settings
from app.knowledge.corpus_loader import load_corpus
from app.knowledge.grounding import available_method, ground
from app.knowledge.lexical import LexicalRetriever, tokenize
from app.knowledge.retriever import RetrievalResult, Retriever


def _retriever(**kwargs) -> LexicalRetriever:
    settings = get_settings()
    corpus_dir = os.path.join(str(settings.kb_dir), "corpus")
    return LexicalRetriever(load_corpus(corpus_dir), **kwargs)


def test_tokenizer_keeps_section_references_whole():
    tokens = tokenize("Notice under section 143(1)(a) of the Income Tax Act")
    assert "143(1)(a)" in tokens
    assert "section" not in tokens  # stopword
    assert "143" not in tokens  # split fragments never appear; whole form only


def test_lexical_ranks_relevant_chunk_first():
    result = _retriever(default_k=4, default_floor=0.25).retrieve(
        "explain 143(1)(a) income mismatch intimation salary"
    )
    assert result.chunks, "relevant query must retrieve at least one chunk"
    assert result.chunks[0].id == "kb-143-1a-mismatch"
    assert not result.below_floor
    assert result.method == "lexical"


def test_lexical_refuses_gibberish():
    result = _retriever().retrieve("quantum banana tango")
    assert result.below_floor is True
    assert result.confidence == 0.0
    assert result.chunks == ()


def test_lexical_respects_top_k():
    result = _retriever().retrieve("income mismatch intimation response", top_k=2)
    assert len(result.chunks) <= 2


def test_ground_reports_method_and_result():
    settings = get_settings()
    # Tests run with no vectors.json and no API key -> lexical is the truth.
    assert available_method(settings) == "lexical"
    result = ground(settings, "explain 143(1)(a) income mismatch intimation salary")
    assert isinstance(result, RetrievalResult)
    assert result.method == "lexical"
    assert result.confidence > 0
    assert not result.below_floor


def test_ground_off_topic_still_honest():
    result = ground(get_settings(), "recipe for mango lassi")
    assert result.method == "lexical"
    assert result.below_floor is True


def test_retriever_load_and_vector_index_consistency():
    settings = get_settings()
    chunks = load_corpus(os.path.join(settings.kb_dir, "corpus"))
    vpath = os.path.join(settings.kb_dir, "vectors.json")
    assert os.path.exists(vpath)

    with open(vpath, encoding="utf-8") as fh:
        payload = json.load(fh)

    # 1. Corpus count == Vector count
    assert len(payload) == len(chunks)

    # 2. IDs match
    corpus_ids = {c.id for c in chunks}
    vector_ids = {entry.get("id") for entry in payload}
    assert vector_ids == corpus_ids

    # 3. Vectors are valid
    for entry in payload:
        vec = entry.get("vector")
        assert isinstance(vec, list)
        assert len(vec) == 1536
        norm = np.linalg.norm(vec)
        assert 0.99 <= norm <= 1.01

    # 4. Retriever.load() succeeds
    retriever = Retriever.load(settings)
    assert retriever is not None

    # 5. Retrieval with vector works
    dummy_query_vector = payload[0]["vector"]
    res = retriever.retrieve(dummy_query_vector, top_k=3)
    assert len(res.chunks) == 3
    assert res.chunks[0].id == payload[0]["id"]

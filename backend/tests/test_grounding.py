"""Grounding must always work and always be honest.

The lexical fallback exists so the confidence gate is enforceable even
without vectors.json or an API key — these tests pin that contract.
"""

import os

from app.config import get_settings
from app.knowledge.corpus_loader import load_corpus
from app.knowledge.grounding import available_method, ground
from app.knowledge.lexical import LexicalRetriever, tokenize
from app.knowledge.retriever import RetrievalResult


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

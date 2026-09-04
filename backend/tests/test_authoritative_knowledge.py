import os

from app.config import get_settings
from app.knowledge.corpus_loader import citations_for, load_corpus
from app.knowledge.lexical import LexicalRetriever


def _retriever():
    settings = get_settings()
    return LexicalRetriever(load_corpus(os.path.join(settings.kb_dir, "corpus")))


def test_authoritative_workflow_queries_retrieve_expected_sources():
    retriever = _retriever()
    assert retriever.retrieve("section 142(1) produce accounts documents written information").chunks[0].id == "kb-142-1-scrutiny-documents"
    assert retriever.retrieve("section 143 scrutiny assessment processing return").chunks[0].source_id == "SEC-143"
    assert retriever.retrieve("section 144 best judgment failure comply 142(1)").chunks[0].id == "kb-144-non-compliance-142"
    assert retriever.retrieve("e-Proceedings submit written response attachment transaction ID").chunks[0].source_id == "EP-MANUAL"


def test_provenance_survives_pack_chunking_and_citation_resolution():
    chunks = load_corpus(os.path.join(get_settings().kb_dir, "corpus"))
    chunk = next(c for c in chunks if c.source_id == "SEC-142")
    assert chunk.document_title == "Section 142 — Inquiry before assessment"
    citation = citations_for((chunk.id,), os.path.join(get_settings().kb_dir, "corpus"))[0]
    assert citation["source_id"] == "SEC-142"
    assert citation["verification_status"] == "VERIFIED_OFFICIAL"
    assert citation["verification_state"] == "Verified"
    assert "why_supports" in citation
    assert citation["source_url"].startswith("https://www.incometaxindia.gov.in/")


def test_pending_is_distinct_from_verified():
    citations = citations_for(("kb-143-1-overview",), os.path.join(get_settings().kb_dir, "corpus"))
    assert citations[0]["verification"] == "pending"
    assert citations[0]["verification_status"] == "PENDING_VERIFICATION"
    assert citations[0]["verification_state"] == "Pending verification"


def test_historical_and_unknown_sources_are_not_preferred_over_current():
    retriever = _retriever()
    result = retriever.retrieve("section 142(1) faceless assessment further evidence")
    assert result.chunks
    assert result.chunks[0].status != "HISTORICAL"


def test_unrelated_query_keeps_existing_refusal_floor():
    result = _retriever().retrieve("quantum banana tango")
    assert result.confidence == 0.0
    assert result.below_floor is True

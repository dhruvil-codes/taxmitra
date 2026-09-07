from app.knowledge.corpus_loader import Chunk, citations_for, parse_chunk
from app.config import get_settings
from app.knowledge.grounding import ground
from app.knowledge.lexical import LexicalRetriever
from app.knowledge.versioning import ACT_1961, ACT_2025, resolve_applicability


def _chunk(identifier: str, text: str, **kwargs) -> Chunk:
    return Chunk(
        id=identifier,
        text=text,
        section=kwargs.pop("section", "142(1)"),
        source_id=identifier,
        official_url="https://www.incometax.gov.in/",
        verification_status="VERIFIED_OFFICIAL",
        **kwargs,
    )


def test_frontmatter_preserves_version_dates_and_workflow_context():
    chunk = parse_chunk(
        """---
id: versioned
publication_date: 2026-01-01
update_date: 2026-09-06
act_version: Income Tax Act, 2025
workflow_context: 139(9), e-Proceedings
---
Current portal guidance.
"""
    )
    assert chunk.publication_date == "2026-01-01"
    assert chunk.update_date == "2026-09-06"
    assert chunk.act_version == "Income Tax Act, 2025"
    assert chunk.workflow_context == ("139(9)", "e-Proceedings")


def test_assessment_year_and_tax_year_resolve_act_version():
    assert resolve_applicability(assessment_year="2025-26").act_version == ACT_1961
    assert resolve_applicability(tax_year="2026-27").act_version == ACT_2025
    assert resolve_applicability(assessment_year="2025-26", tax_year="2026-27").ambiguous


def test_retrieval_excludes_superseded_and_prefers_current_source():
    retriever = LexicalRetriever(
        (
            _chunk("old", "section 142(1) scrutiny documents", status="SUPERSEDED"),
            _chunk("current", "section 142(1) scrutiny documents current official guidance"),
        ),
        default_floor=0.01,
    )
    result = retriever.retrieve("section 142(1) scrutiny documents")
    assert result.chunks[0].id == "current"
    assert all(chunk.id != "old" for chunk in result.chunks)


def test_act_version_context_does_not_mix_1961_and_2025_guidance():
    retriever = LexicalRetriever(
        (
            _chunk("old-act", "section 139(9) defective return response", act_version=ACT_1961),
            _chunk("new-act", "section 139(9) defective return response", act_version=ACT_2025),
        ),
        default_floor=0.01,
    )
    result = retriever.retrieve(
        "section 139(9) defective return response",
        assessment_year="2025-26",
    )
    assert result.chunks
    assert all(chunk.id == "old-act" for chunk in result.chunks)


def test_workflow_context_filters_when_sources_declare_context():
    retriever = LexicalRetriever(
        (
            _chunk("scrutiny", "documents information response", workflow_context=("142(1)",)),
            _chunk("defect", "documents information response", workflow_context=("139(9)",)),
        ),
        default_floor=0.01,
    )
    result = retriever.retrieve("documents information response", workflow_context="139(9)")
    assert result.chunks[0].id == "defect"


def test_conflicting_applicability_is_refused():
    applicability = resolve_applicability(assessment_year="2025-26", tax_year="2026-27")
    assert applicability.ambiguous is True


def test_grounding_surfaces_ambiguous_context_as_safe_refusal():
    result = ground(
        get_settings(),
        "section 139(9) defective return",
        assessment_year="2025-26",
        tax_year="2026-27",
    )
    assert result.ambiguous is True
    assert result.below_floor is True
    assert result.chunks == ()
    assert "conflicting" in result.reason.lower()


def test_new_official_sources_have_provenance_and_current_status():
    import os
    citation = citations_for(("v2-tax-credit-mismatch-current",), os.path.join(get_settings().kb_dir, "corpus"))[0]
    assert citation["official_url"].startswith("https://www.incometax.gov.in/")
    assert citation["publication_date"] == "2026-01-01"
    assert citation["update_date"] == "2026-09-06"
    assert citation["status"] == "CURRENT"
    assert citation["verification_status"] == "VERIFIED_OFFICIAL"

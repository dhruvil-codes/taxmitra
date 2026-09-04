"""Contract tests for user-facing tax terminology and tone."""

import json
from pathlib import Path

from app.rules.refusal import build_refusal
from app.rules.scrutiny import _REQUEST_LIBRARY
from app.rules.terminology import TAX_TERMS, TERMINOLOGY_GUIDANCE, term
from app.rules.notice_types import NoticeCategory


def test_canonical_terms_have_english_and_hindi_labels():
    for key, labels in TAX_TERMS.items():
        assert labels["en"]
        assert labels["hi"]
        assert term(key, "en") == labels["en"]
        assert term(key, "hi") == labels["hi"]


def test_scrutiny_explanations_use_precise_tax_vocabulary():
    for request in _REQUEST_LIBRARY.values():
        assert request["plain"]["en"]
        assert "officer wants" not in request["plain"]["en"].lower()
        assert "Assessing Officer" in request["plain"]["en"] or request is _REQUEST_LIBRARY["req_notice_document"]

    assert "professionalial" not in str(_REQUEST_LIBRARY).lower()
    assert "professional receipts" in str(_REQUEST_LIBRARY)


def test_income_mismatch_fallback_separates_mismatch_from_final_liability():
    root = Path(__file__).parents[1]
    fallback = json.loads(
        (root / "app" / "static_fallbacks" / "explanation_income_mismatch_143_1a_en.json").read_text()
    )
    assert "return of income" in fallback["plain_language"]
    assert "proposed adjustment" in fallback["plain_language"]
    assert "not, by itself, a final conclusion" in fallback["what_this_does_not_mean"]
    assert "don't match" not in fallback["plain_language"]


def test_refusal_is_specific_and_does_not_use_reassurance_copy():
    refusal = build_refusal(NoticeCategory.UNSUPPORTED)
    assert "outside Tax Mitra's supported workflows" in refusal["headline"]["en"]
    assert "Don't worry" not in str(refusal)
    assert "We've got you" not in str(refusal)
    assert "guess" not in refusal["why"]["en"].lower()


def test_explanation_prompt_requires_terminology_and_boundaries():
    assert "Assessment Year" in TERMINOLOGY_GUIDANCE
    assert "proposed adjustment" in TERMINOLOGY_GUIDANCE
    assert "final tax demand" in TERMINOLOGY_GUIDANCE

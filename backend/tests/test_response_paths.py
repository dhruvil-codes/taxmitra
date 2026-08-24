"""Totality + determinism of the response-path resolver — all 27 answer
combinations must resolve, identically, every time."""

import itertools

from app.rules.checklists import known_document_ids
from app.rules.notice_types import NoticeCategory
from app.rules.response_paths import (
    EVIDENCE_AVAILABLE,
    EVIDENCE_MISSING,
    POSITION_AGREE,
    POSITION_DISAGREE,
    POSITION_NOT_SURE,
    build_draft,
    evidence_from_answers,
    resolve_path,
)
from app.data_store import get_citizen, get_notice, load_draft_templates

CAT = NoticeCategory.INCOME_MISMATCH_143_1A
ANSWER_VALUES = ("yes", "no", "unsure")
QUESTION_IDS = ("q1_received", "q2_in_return", "q3_documents")

EXPECTED_PATHS = {
    ("no", "yes"): "disagree_not_received",
    ("no", "no"): "disagree_not_received",
    ("no", "unsure"): "disagree_not_received",
    ("unsure", "yes"): "not_sure_verify_payer",
    ("unsure", "no"): "not_sure_verify_payer",
    ("unsure", "unsure"): "not_sure_verify_payer",
    ("yes", "yes"): "disagree_already_reported",
    ("yes", "no"): "agree_report_now",
    ("yes", "unsure"): "not_sure_check_return",
}


def all_combos():
    return [dict(zip(QUESTION_IDS, values)) for values in itertools.product(ANSWER_VALUES, repeat=3)]


def test_every_answer_combination_resolves():
    for answers in all_combos():
        path = resolve_path(CAT, answers)
        assert path is not None, answers
        assert path.position in (POSITION_AGREE, POSITION_DISAGREE, POSITION_NOT_SURE)
        assert path.path_id == EXPECTED_PATHS[(answers["q1_received"], answers["q2_in_return"])]


def test_resolution_is_deterministic():
    answers = {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"}
    assert resolve_path(CAT, answers) == resolve_path(CAT, answers)


def test_unsupported_category_returns_none():
    assert resolve_path(NoticeCategory.UNSUPPORTED, dict.fromkeys(QUESTION_IDS, "yes")) is None


def test_evidence_overlay_inserts_howto_document():
    with_docs = resolve_path(CAT, {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"})
    without = resolve_path(CAT, {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "no"})
    assert evidence_from_answers(with_docs and {"q3_documents": "yes"}) == EVIDENCE_AVAILABLE
    assert without.checklist_ids[0] == "doc_ais_download"
    assert "doc_ais_download" not in with_docs.checklist_ids


def test_checklist_ids_are_known_documents():
    known = known_document_ids()
    for answers in all_combos():
        path = resolve_path(CAT, answers)
        assert set(path.checklist_ids) <= known
        assert len(path.checklist_ids) == len(set(path.checklist_ids))


def test_build_draft_fills_every_slot():
    notice = get_notice("N-2026-001")
    citizen = get_citizen(notice["citizen_id"])
    templates = load_draft_templates()
    from datetime import date

    for answers in all_combos():
        path = resolve_path(CAT, answers)
        draft = build_draft(templates[path.draft_template_id], notice, citizen, answers, date(2026, 9, 12))
        assert "{" not in draft, f"unfilled slot in template {path.draft_template_id}"
        assert draft.startswith("Subject: Response to intimation under section 143(1)(a)")
        assert "₹45,000" in draft

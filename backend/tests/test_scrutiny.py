from fastapi.testclient import TestClient

from app.data_store import get_notice
from app.extraction.notices import confirmed_requests, extract_notice_requests
from app.main import app
from app.rules.notice_types import NoticeCategory, classify_notice
from app.rules.response_paths import resolve_path
from app.rules.scrutiny import build_scrutiny_requests, resolve_scrutiny, scrutiny_questions

client = TestClient(app)


def _answers(value: str = "yes") -> dict[str, str]:
    questions = client.get("/api/scrutiny/N-2026-003/questions").json()["questions"]
    return {question["id"]: value for question in questions}


def test_142_notice_structure_and_extraction_boundary():
    notice = get_notice("N-2026-003")
    assert classify_notice(notice) == NoticeCategory.SCRUTINY_142_1
    extracted = extract_notice_requests(notice)
    assert extracted.notice_id == "N-2026-003"
    assert extracted.source_type == "synthetic_pdf"
    assert extracted.requires_human_confirmation is True
    assert len(extracted.requests) == 8
    assert confirmed_requests(extracted, confirmed=False) == ()
    assert len(confirmed_requests(extracted, confirmed=True)) == 8


def test_scrutiny_requests_are_enriched_and_cited():
    response = client.get("/api/scrutiny/N-2026-003/requests", params={"locale": "en"})
    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["extraction"]["requires_human_confirmation"] is True
    assert len(body["requests"]) == 8
    first = body["requests"][0]
    assert first["id"] == "req_computation_income"
    assert first["original_text"]
    assert first["plain_language_explanation"]["en"]
    assert first["plain_language_explanation"]["hi"]
    assert first["why_required"]["en"]
    assert first["required_evidence"]
    assert first["response_section"] == "Computation of total income"
    assert first["citations"][0]["id"] == "kb-142-1-scrutiny-documents"
    assert first["category"] == "income_computation"
    assert first["page"] == 2
    assert "Detailed computation" in first["what_department_is_asking"]
    assert first["status"] == "not_started"
    assert first["clarifying_questions"]
    assert body["grounding"]["method"] in ("lexical", "embedding")
    assert body["grounding"]["below_floor"] is False


def test_dynamic_questions_are_derived_from_requests():
    requests = build_scrutiny_requests(get_notice("N-2026-003"))
    questions = scrutiny_questions(requests)
    assert len(questions) == len(requests) == 8
    assert {q.request_id for q in questions} == {r.id for r in requests}

    body = client.get("/api/scrutiny/N-2026-003/questions", params={"locale": "hi"}).json()
    assert body["supported"] is True
    assert len(body["questions"]) == 8
    assert body["questions"][0]["id"] == "evidence_req_computation_income"
    assert {option["id"] for option in body["questions"][0]["options"]} == {"yes", "no", "unsure"}
    assert body["questions"][0]["text"]


def test_evidence_mapping_is_request_scoped_and_keeps_missing_items_visible():
    response = client.get("/api/scrutiny/N-2026-003/requests")
    body = response.json()
    assert body["evidence"]
    cash = [item for item in body["evidence"] if item["request_id"] == "req_cash_deposits"]
    assert any(item["document_name"]["en"] == "Cash book, if maintained" and item["requirement_level"] == "possibly_relevant" for item in cash)
    assert all(item["status"] == "not_sure" for item in cash)
    projected = client.post("/api/scrutiny/N-2026-003/evidence", json={"statuses": {cash[0]["document_id"]: "have"}})
    assert projected.status_code == 200
    assert projected.json()["storage"] == "local_or_browser_only"
    assert any(item["status"] == "not_sure" for item in projected.json()["missing_evidence"])


def test_resolve_all_yes_generates_ready_checklist_and_draft():
    response = client.post(
        "/api/scrutiny/resolve",
        json={"notice_id": "N-2026-003", "answers": _answers("yes")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["path"]["path_id"] == "ready_to_respond"
    assert body["path"]["professional_help_recommended"] is False
    assert len(body["checklist"]) == 8
    assert all(item["status"] == "yes" for item in body["checklist"])
    assert all(item["workflow_status"] == "ready_for_response" for item in body["checklist"])
    assert "Computation of total income" in body["draft"]
    assert "Tax Mitra has not verified taxpayer facts" in body["draft"]
    assert body["official_step"]["url"].startswith("https://www.incometax.gov.in")


def test_final_review_requires_explicit_approval_and_preserves_handoff_boundary():
    resolved = client.post("/api/scrutiny/resolve", json={"notice_id": "N-2026-003", "answers": _answers("yes")}).json()
    blocked = client.post("/api/scrutiny/N-2026-003/review", json={"answers": _answers("yes"), "draft": resolved["draft"], "approved": False})
    assert blocked.status_code == 200
    assert blocked.json()["handoff_allowed"] is False
    approved = client.post("/api/scrutiny/N-2026-003/review", json={"answers": _answers("yes"), "draft": resolved["draft"], "approved": True})
    assert approved.status_code == 200
    assert approved.json()["handoff_allowed"] is True
    assert "does not submit" in approved.json()["boundary"]


def test_resolve_no_marks_missing_evidence_without_inventing_facts():
    answers = _answers("yes")
    answers["evidence_req_cash_deposits"] = "no"
    body = client.post("/api/scrutiny/resolve", json={"notice_id": "N-2026-003", "answers": answers}).json()
    assert body["path"]["path_id"] == "needs_evidence"
    cash = next(item for item in body["checklist"] if item["request_id"] == "req_cash_deposits")
    assert cash["status"] == "no"
    assert cash["title"]["en"].startswith("Clarify discrepancy:")
    assert "does not match my records" in body["draft"]


def test_resolve_unsure_takes_safe_review_path():
    answers = _answers("yes")
    answers["evidence_req_significant_transactions"] = "unsure"
    body = client.post("/api/scrutiny/resolve", json={"notice_id": "N-2026-003", "answers": answers}).json()
    assert body["path"]["path_id"] == "needs_review"
    assert body["path"]["professional_help_recommended"] is True
    assert "requires verification from my records" in body["draft"]
    assert "professional review" in body["draft"]


def test_scrutiny_refuses_when_extraction_is_not_confirmed():
    response = client.post(
        "/api/scrutiny/resolve",
        json={"notice_id": "N-2026-003", "answers": {}, "extraction_confirmed": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is False
    assert "confirmed list" in body["headline"]["en"]


def test_scrutiny_validation_and_routing_errors():
    missing = client.post("/api/scrutiny/resolve", json={"notice_id": "N-2026-003", "answers": {}})
    assert missing.status_code == 422
    invalid = _answers("yes")
    invalid["evidence_req_balance_sheet"] = "maybe"
    assert client.post("/api/scrutiny/resolve", json={"notice_id": "N-2026-003", "answers": invalid}).status_code == 422
    unexpected = _answers("yes")
    unexpected["stale_answer"] = "no"
    assert client.post("/api/scrutiny/resolve", json={"notice_id": "N-2026-003", "answers": unexpected}).status_code == 422
    assert client.get("/api/scrutiny/N-2026-001/requests").status_code == 400
    assert client.get("/api/workflow/questions/N-2026-003").status_code == 400
    assert client.get("/api/ai/explanation/N-2026-003").status_code == 400


def test_existing_143_regression_still_resolves_same_path():
    path = resolve_path(
        NoticeCategory.INCOME_MISMATCH_143_1A,
        {"q1_received": "yes", "q2_in_return": "yes", "q3_documents": "yes"},
    )
    assert path.path_id == "disagree_already_reported"
    assert client.get("/api/ai/explanation/N-2026-001").status_code == 200

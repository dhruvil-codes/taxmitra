"""Coverage for the simplified deterministic 142(1) question plan."""

from fastapi.testclient import TestClient

from app.main import app
from app.data_store import get_notice
from app.rules.scrutiny import build_scrutiny_requests, minimum_question_plan

client = TestClient(app)


def test_eight_requests_do_not_become_eight_questions():
    notice = get_notice("N-2026-003")
    requests = build_scrutiny_requests(notice)
    plan = minimum_question_plan(requests)

    assert len(requests) == 8
    assert len(plan) < len(requests)
    assert {"cash_deposit_source", "significant_transaction_explanation"} <= {q.id for q in plan}
    assert "evidence_req_balance_sheet" not in {q.id for q in plan}


def test_question_plan_api_exposes_structured_requests_and_grounding():
    body = client.get("/api/scrutiny/N-2026-003/question-plan").json()

    assert body["supported"] is True
    assert body["request_count"] == 8
    assert body["question_count"] < body["request_count"]
    cash = next(q for q in body["questions"] if q["question_id"] == "cash_deposit_source")
    assert cash["type"] == "single_choice"
    assert cash["required"] is True
    assert {option["id"] for option in cash["options"]} >= {"business_income", "loan", "unsure"}

    request = next(r for r in client.get("/api/scrutiny/N-2026-003/requests").json()["requests"] if r["id"] == "req_balance_sheet")
    assert request["original_text"].startswith("Balance sheet")
    assert request["technical_term"] == "Balance sheet"
    assert request["source_ids"]


def test_conditional_follow_up_only_appears_for_relevant_source():
    body = client.post(
        "/api/scrutiny/question-plan",
        json={"notice_id": "N-2026-003", "answers": {"cash_deposit_source": "loan"}},
    ).json()
    ids = {question["question_id"] for question in body["questions"]}
    assert "cash_loan_records" in ids
    assert "cash_business_income_records" not in ids


def test_not_sure_is_preserved_as_its_own_option():
    body = client.get("/api/scrutiny/N-2026-003/question-plan").json()
    cash = next(q for q in body["questions"] if q["question_id"] == "cash_deposit_source")
    assert next(option for option in cash["options"] if option["id"] == "unsure")["label"] == "Not sure"

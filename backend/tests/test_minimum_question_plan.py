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


def test_significant_transaction_explanation_offers_backend_defined_choices_with_other():
    body = client.get("/api/scrutiny/N-2026-003/question-plan").json()
    question = next(q for q in body["questions"] if q["question_id"] == "significant_transaction_explanation")

    assert question["type"] == "choice_with_other"
    assert [option["id"] for option in question["options"]] == [
        "business_transactions",
        "loan_or_borrowing",
        "personal_or_family_transfer",
        "something_else",
    ]
    assert next(option for option in question["options"] if option["id"] == "something_else")["label"] == "Something else"


def test_universal_workflow_contract_serves_the_same_choice_with_other_schema():
    body = client.get("/api/workflow/questions/N-2026-003").json()
    question = next(q for q in body["questions"] if q.get("question_id") == "significant_transaction_explanation")

    assert (question.get("type") or question.get("question_type")) == "choice_with_other"
    assert {option["id"] for option in question["options"]} == {
        "business_transactions",
        "loan_or_borrowing",
        "personal_or_family_transfer",
        "something_else",
    }


def test_minimum_resolution_requires_only_plan_answers_and_maps_evidence():
    answers = {
        "cash_deposit_source": "savings",
        "significant_transaction_explanation": {"choice": "business_transactions", "other": ""},
        "other_request_details": "No additional request information",
    }
    body = client.post("/api/scrutiny/resolve-minimum", json={"notice_id": "N-2026-003", "answers": answers}).json()

    assert body["path"]["path_id"] == "ready_to_respond"
    assert len(body["evidence"]) > 8
    assert any(item["request_id"] == "req_balance_sheet" for item in body["evidence"])
    assert "Balance sheet" in body["draft"]
    assert "Business transactions recorded in my books" in body["draft"]


def test_something_else_requires_other_text_and_flows_into_the_draft():
    missing_other = {
        "cash_deposit_source": "savings",
        "significant_transaction_explanation": {"choice": "something_else", "other": "   "},
        "other_request_details": "No additional request information",
    }
    assert client.post("/api/scrutiny/resolve-minimum", json={"notice_id": "N-2026-003", "answers": missing_other}).status_code == 422

    explained = {**missing_other, "significant_transaction_explanation": {"choice": "something_else", "other": "Agricultural income receipts"}}
    body = client.post("/api/scrutiny/resolve-minimum", json={"notice_id": "N-2026-003", "answers": explained}).json()
    assert body["path"]["path_id"] == "ready_to_respond"
    assert "Agricultural income receipts" in body["draft"]


def test_invalid_choice_for_significant_transaction_explanation_is_rejected():
    answers = {
        "cash_deposit_source": "savings",
        "significant_transaction_explanation": {"choice": "not_a_real_option", "other": ""},
        "other_request_details": "No additional request information",
    }
    assert client.post("/api/scrutiny/resolve-minimum", json={"notice_id": "N-2026-003", "answers": answers}).status_code == 422


def test_workflow_resolve_accepts_typed_choice_with_other_answer():
    answers = {
        "cash_deposit_source": "savings",
        "significant_transaction_explanation": {"choice": "loan_or_borrowing", "other": ""},
        "other_request_details": "No additional request information",
    }
    body = client.post("/api/workflow/resolve", json={"notice_id": "N-2026-003", "answers": answers}).json()

    assert body["supported"] is True
    assert "Loan received or repaid" in body["draft"]


def test_regression_workflow_resolve_succeeds_without_conditional_follow_up_answers():
    """Regression: /api/workflow/resolve must not 422 when conditional follow-up answers
    (e.g. cash_business_income_records) are absent.

    These follow-up questions are added to the plan only AFTER the parent answer
    (cash_deposit_source=business_income) is submitted.  The initial question set
    shown to the user does NOT include them, so their absence must be accepted and
    treated as 'unsure' by the resolver.

    This was the root cause of the 'We could not resolve this workflow safely.'
    error shown after the guided 142(1) question flow completed.
    """
    # User answers cash_deposit_source=business_income but never saw the
    # conditional follow-up question cash_business_income_records.
    answers = {
        "cash_deposit_source": "business_income",
        "significant_transaction_explanation": {"choice": "business_transactions", "other": ""},
        "other_request_details": "No additional request information",
    }
    response = client.post("/api/workflow/resolve", json={"notice_id": "N-2026-003", "answers": answers})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body.get("supported") is True, f"Expected supported=True: {body}"
    assert "draft" in body

    # Loan source similarly has a conditional cash_loan_records follow-up.
    answers_loan = {
        "cash_deposit_source": "loan",
        "significant_transaction_explanation": {"choice": "loan_or_borrowing", "other": ""},
        "other_request_details": "No additional request information",
    }
    response_loan = client.post("/api/workflow/resolve", json={"notice_id": "N-2026-003", "answers": answers_loan})
    assert response_loan.status_code == 200, f"Expected 200 for loan, got {response_loan.status_code}: {response_loan.text}"
    assert response_loan.json().get("supported") is True


def test_minimum_review_blocks_uncertainty_and_allows_handoff_after_evidence_review():
    answers = {
        "cash_deposit_source": "unsure",
        "significant_transaction_explanation": {"choice": "personal_or_family_transfer", "other": ""},
        "other_request_details": "Need taxpayer review",
    }
    resolved = client.post("/api/scrutiny/resolve-minimum", json={"notice_id": "N-2026-003", "answers": answers}).json()
    blocked = client.post(
        "/api/scrutiny/N-2026-003/review-minimum",
        json={"notice_id": "N-2026-003", "answers": answers, "draft": resolved["draft"], "approved": True},
    ).json()
    assert blocked["handoff_allowed"] is False

    ready_answers = {**answers, "cash_deposit_source": "savings"}
    ready = client.post("/api/scrutiny/resolve-minimum", json={"notice_id": "N-2026-003", "answers": ready_answers}).json()
    statuses = {item["document_id"]: "have" for item in ready["evidence"]}
    approved = client.post(
        "/api/scrutiny/N-2026-003/review-minimum",
        json={"notice_id": "N-2026-003", "answers": ready_answers, "draft": ready["draft"], "approved": True, "document_statuses": statuses},
    ).json()
    assert approved["handoff_allowed"] is True

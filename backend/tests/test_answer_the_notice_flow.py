"""Test suite for the 'Answer the Notice' Questions -> Response flow.

Verifies:
1. 1:1 request-to-question generation from actual extracted notice requests.
2. Distinct separation between 'Understand your situation' and 'Answer the Notice'.
3. Passing request answers into response generation across 142(1), 133(6), 143(1)(a), and 139(9).
4. Bilingual generation (en and hi).
5. Never inventing requests not present in the notice.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.data_store import get_notice
from app.workflows.notice_requests import (
    get_notice_extracted_requests,
    build_answer_the_notice_questions,
    extract_taxpayer_request_answer,
    format_itemized_request_responses,
)
from app.workflows.handlers import (
    get_workflow_handler,
    Scrutiny142Handler,
    InformationRequest1336Handler,
    IncomeMismatch143Handler,
    DefectiveReturn1399Handler,
)
from app.rules.letter_templates import format_formal_reply_letter

client = TestClient(app)


def test_142_1_generates_exact_eight_notice_questions_and_incorporates_answers():
    notice = get_notice("N-2026-003")
    assert notice is not None
    requests = get_notice_extracted_requests(notice)
    assert len(requests) == 8  # 8 requests extracted from N-2026-003

    # 1:1 Rule: 8 requests must become exactly 8 taxpayer-facing questions
    notice_questions = build_answer_the_notice_questions(requests, locale="en")
    assert len(notice_questions) == 8

    # Each question clearly identifies the requisition and provides options & details
    first_q = notice_questions[0]
    assert first_q["section"] == "answer_the_notice"
    assert "Requisition 1" in first_q["text"]
    assert first_q["department_request"]["original_text"] == requests[0]["original_text"]
    assert first_q["allow_details"] is True
    assert {opt["id"] for opt in first_q["options"]} == {"provide", "partial", "not_applicable", "explain"}

    # Simulate taxpayer answering requests A, B, C...
    answers = {
        "cash_deposit_source": "business_income",
        "notice_req_req_computation_income": {
            "choice": "provide",
            "details": "Total income computation of Rs. 12,40,000 certified by CA enclosed as Annexure 1.",
        },
        "notice_req_req_balance_sheet": {
            "choice": "provide",
            "details": "Audited balance sheet as of 31/03/2024 enclosed.",
        },
        "notice_req_req_bank_statements": {
            "choice": "partial",
            "details": "Bank statement of HDFC Bank provided; ICICI Bank statement requested from branch.",
        },
    }

    # Generate response letter using format_formal_reply_letter
    from app.rules.scrutiny import build_scrutiny_requests, resolve_minimum_scrutiny
    scrutiny_reqs = build_scrutiny_requests(notice)
    letter = format_formal_reply_letter(notice, scrutiny_reqs, answers)

    # Taxpayer's details appear as prose body in the numbered points (no labels)
    assert "Total income computation of Rs. 12,40,000 certified by CA enclosed as Annexure 1." in letter
    assert "Audited balance sheet as of 31/03/2024 enclosed." in letter
    assert "Bank statement of HDFC Bank provided; ICICI Bank statement requested from branch." in letter
    # Authentic letter structure: numbered points + annexure references + closing
    assert "(As per Annexure" in letter
    assert "Thanking you," in letter
    assert "Yours faithfully," in letter


def test_133_6_generates_exact_three_questions_and_incorporates_answers():
    notice = get_notice("N-2026-006")
    assert notice is not None
    requests = get_notice_extracted_requests(notice)
    assert len(requests) == 3  # 3 requests extracted from N-2026-006

    # 1:1 Rule
    notice_questions = build_answer_the_notice_questions(requests, locale="en")
    assert len(notice_questions) == 3

    # Answers to requests A, B, C
    answers = {
        "information_record_confirmed": "yes",
        "notice_req_req_interest_income_explanation": {
            "choice": "provide",
            "details": "Interest of Rs. 1,25,000 pertains to fixed deposits with Demo Financial Services and was declared under Other Sources.",
        },
        "notice_req_req_business_expenses_documents": {
            "choice": "provide",
            "details": "Ledgers and vouchers for Rs. 3,50,000 expenses enclosed.",
        },
        "notice_req_req_bank_accounts_details": {
            "choice": "complete",
            "details": "Details of two active savings bank accounts enclosed.",
        },
    }

    handler = InformationRequest1336Handler()
    result = handler.resolve(notice, answers)
    assert result["supported"] is True
    draft = result["draft"]

    # Draft explicitly addresses all 3 requests with taxpayer's answers
    assert "Interest of Rs. 1,25,000 pertains to fixed deposits" in draft
    assert "Ledgers and vouchers for Rs. 3,50,000 expenses enclosed." in draft
    assert "Details of two active savings bank accounts enclosed." in draft


def test_143_1a_generates_one_question_and_incorporates_answer():
    notice = get_notice("N-2026-001")
    assert notice is not None
    requests = get_notice_extracted_requests(notice)
    assert len(requests) == 1

    # 1:1 Rule: 1 request becomes 1 question
    notice_questions = build_answer_the_notice_questions(requests, locale="en")
    assert len(notice_questions) == 1
    assert notice_questions[0]["department_request"]["title"] == "Proposed adjustment for interest income mismatch"

    # Answer provided for the mismatch request
    answers = {
        "q1_received": "yes",
        "q2_in_return": "yes",
        "q3_documents": "yes",
        "notice_req_req_interest_mismatch_143_1a": {
            "choice": "explain",
            "details": "Interest income of Rs. 45,000 from Demo Bharat Bank was already included under Schedule OS (Item 1(a)(i)) in the filed ITR.",
        },
    }

    handler = IncomeMismatch143Handler()
    result = handler.resolve(notice, answers)
    assert result["supported"] is True
    draft = result["draft"]

    # Draft uses formal letter format with numbered points
    assert "Interest income of Rs. 45,000 from Demo Bharat Bank was already included" in draft
    assert "(As per Annexure" in draft or "Thanking you," in draft


def test_139_9_partial_support_generates_three_defect_questions_and_incorporates_answers():
    notice = get_notice("N-2026-004")
    assert notice is not None
    requests = get_notice_extracted_requests(notice)
    assert len(requests) == 3

    # 1:1 Rule: 3 defects become 3 questions
    notice_questions = build_answer_the_notice_questions(requests, locale="en")
    assert len(notice_questions) == 3

    answers = {
        "defect_extraction_confirmed": "yes",
        "defect_position": "agree",
        "correction_route": "online_correction",
        "notice_req_req_tds_credit_defect": {
            "choice": "provide",
            "details": "Updated TDS TAN and challan serial numbers matching Form 26AS.",
        },
        "notice_req_req_bank_account_defect": {
            "choice": "provide",
            "details": "Validated primary savings bank account details added in profile.",
        },
        "notice_req_req_balance_sheet_defect": {
            "choice": "provide",
            "details": "Uploaded business balance sheet schedule in corrected return.",
        },
    }

    handler = DefectiveReturn1399Handler()
    result = handler.resolve(notice, answers)
    assert result["supported"] is True
    draft = result["draft"]

    # Draft explicitly addresses each defect
    assert "Itemized Defect Responses:" in draft
    assert "Updated TDS TAN and challan serial numbers matching Form 26AS." in draft
    assert "Validated primary savings bank account details added in profile." in draft
    assert "Uploaded business balance sheet schedule in corrected return." in draft


def test_hindi_localization_of_answer_the_notice():
    notice = get_notice("N-2026-006")
    requests = get_notice_extracted_requests(notice)
    hi_questions = build_answer_the_notice_questions(requests, locale="hi")

    assert len(hi_questions) == 3
    assert "मांग 1" in hi_questions[0]["text"]
    assert hi_questions[0]["section_title"]["hi"] == "नोटिस का जवाब दें"
    assert hi_questions[0]["options"][0]["label"] == "मेरे पास यह रिकॉर्ड है और मैं पूरा विवरण प्रदान कर सकता हूँ"


def test_workflow_api_returns_both_situation_and_notice_questions():
    response = client.get("/api/workflow/questions/N-2026-006")
    assert response.status_code == 200
    data = response.json()

    assert "situation_questions" in data
    assert "notice_questions" in data
    assert len(data["notice_questions"]) == 3
    assert data["notice_questions"][0]["section"] == "answer_the_notice"


def test_notice_workflow_contract_includes_separated_question_sections():
    response = client.get("/api/notices/N-2026-003/workflow")
    assert response.status_code == 200
    contract = response.json()["contract"]

    assert "situation_questions" in contract
    assert "notice_questions" in contract
    assert len(contract["notice_questions"]) == 8
    assert len(contract["requests"]) == 8

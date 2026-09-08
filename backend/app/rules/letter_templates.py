"""Authentic Income Tax response letter generator modeled after real taxpayer submissions.

Reference format: 142(1) reply letter with numbered points, annexure references,
and CA-style prose — as used by practicing chartered accountants in India.
"""

from __future__ import annotations

from datetime import date
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CHOICE_POSITION_LABELS: dict[str, str] = {
    "provide": "I have the records and can provide full details.",
    "full": "I have the records and can provide full details.",
    "complete": "I have the records and can provide full details.",
    "partial": "I can provide partial information; some records are being compiled.",
    "not_applicable": "This item is not applicable to me for the above assessment year.",
    "explain": "I wish to submit the following explanation in response to this requisition.",
    "dispute": "I respectfully submit that the Department's position on this point does not match my records, and I am enclosing the relevant evidence in support.",
    "unsure": "I am reviewing my records and will provide the relevant documents upon verification.",
}


def _choice_to_prose(choice: str | None) -> str:
    """Convert an answer-choice id to authentic CA-style prose."""
    if not choice:
        return ""
    return _CHOICE_POSITION_LABELS.get(choice, "")


def _annexure_label(index: int) -> str:
    """Return the standard Indian CA-style annexure reference."""
    return f"(As per Annexure — {index})"


def _annexure_name_for(req_title: str, req_cat: str, index: int) -> str:
    """Derive a descriptive annexure name from the request."""
    cat_names: dict[str, str] = {
        "computation": "Copy of Computation of total income & return acknowledgment",
        "balance_sheet": "Copy of Complete Balance Sheet and Profit & Loss statement",
        "profit_loss": "Copy of Profit & Loss statement",
        "bank_statements": "Copy of Bank Statement(s) for the relevant assessment year",
        "cash_deposits": "Bank Statement and Cash Ledger copy",
        "credits_debits": "Statement of significant transactions and supporting ledgers",
        "tds_mismatch": "Copy of Form 26AS / AIS and TDS certificates",
        "deductions_exemptions": "Supporting records for deductions and exemptions claimed",
    }
    if req_cat in cat_names:
        return cat_names[req_cat]
    return f"Supporting records for {req_title}"


# ---------------------------------------------------------------------------
# Request field accessor — handles both dict and dataclass requests
# ---------------------------------------------------------------------------

def _req(request: Any, *keys: str, default: str = "") -> str:
    """Read the first matching field from a request that may be a dict or object."""
    for key in keys:
        if isinstance(request, dict):
            val = request.get(key, "")
        else:
            val = getattr(request, key, "")
        if val:
            return str(val)
    return default


# ---------------------------------------------------------------------------
# Main letter formatter
# ---------------------------------------------------------------------------

def format_formal_reply_letter(
    notice: dict[str, Any],
    requests: list[Any] | tuple[Any, ...],
    answers: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
    taxpayer_name: str | None = None,
    pan: str | None = None,
    due_date: str | None = None,
    explanation_fn: Any = None,
    other_fn: Any = None,
) -> str:
    """Format an authentic, professional Income Tax reply letter.

    Matches the real-world format used by chartered accountants in India
    for 142(1) / 133(6) / 143(1)(a) scrutiny responses, as shown in the
    reference letter:

        To
        Assessment Unit / Verification Unit / Technical Unit / Review Unit
        Income Tax Department

        Dear Sir/Madam,

        Ref:  [Taxpayer Name]  PAN: [PAN]
              ASSESSMENT YEAR: [AY]
              DIN: [DIN/reference]
        Sub:  Reply in accordance with Notice under Section [section] of the I. T. Act

        [opening paragraph]

        1.  [taxpayer's narrative for request 1]
            [annexure reference]

        ...

        Thanking you,
        Yours faithfully,
        ([Name])
    """
    section = notice.get("section") or "142(1)"
    official_ref = notice.get("official_reference") or notice.get("id") or "DIN-DEMO"
    assessment_year = notice.get("assessment_year") or "2024-25"
    issue_date = notice.get("issue_date") or date.today().strftime("%d/%m/%Y")
    today_str = date.today().strftime("%d/%m/%Y")
    name = taxpayer_name or notice.get("taxpayer_name") or "Taxpayer"
    pan_no = pan or notice.get("pan") or "[PAN as per e-Filing profile]"

    # ------------------------------------------------------------------ header
    lines: list[str] = [
        f"Date: - {today_str}",
        "",
        "To",
        "Assessment Unit / Verification Unit / Technical Unit / Review Unit",
        "Income Tax Department",
        "",
        "Dear Sir/Madam,",
        "",
        f"Ref:  {name}  PAN: {pan_no}",
        f"      ASSESSMENT YEAR: {assessment_year}",
        f"      DIN: {official_ref}",
        f"Sub:  Reply in accordance with Notice under Section {section} of the I. T. Act",
        "",
        "With reference to the above subject, I wish to state as under:",
        "",
        f"I have received your notice u/s {section} of I.T. Act 1961 dated {issue_date}. "
        "In response to the questionnaire as per the Notice, I am submitting the following details.",
        "",
    ]

    annexure_counter = 1
    annexure_list: list[str] = []

    from app.workflows.notice_requests import extract_taxpayer_request_answer

    source = answers.get("cash_deposit_source")
    sig_ans = answers.get("significant_transaction_explanation")
    other_ans = answers.get("other_request_details")

    # ------------------------------------------------ numbered request points
    for index, request in enumerate(requests, start=1):
        req_id = _req(request, "id", "request_id") or f"req-{index}"
        req_title = _req(
            request,
            "response_section", "technical_term", "what_department_is_asking", "category"
        ) or f"Requisition {index}"
        req_cat = _req(request, "category")

        # Taxpayer's "Answer the Notice" answer
        ans_choice_raw, ans_details = extract_taxpayer_request_answer(req_id, answers)

        # Derive the choice id cleanly (may come as a readable label or raw id)
        choice_id: str | None = None
        if isinstance(answers.get(f"notice_req_{req_id}"), dict):
            choice_id = answers[f"notice_req_{req_id}"].get("choice")

        # Build the prose body for this numbered point
        body_lines: list[str] = []

        # Primary: use the taxpayer's free-text details as the narrative (most authentic)
        if ans_details and ans_details.strip():
            body_lines.append(ans_details.strip())

        # If no free-text, fall back to category-specific standard phrases
        elif req_cat == "cash_deposits" and source and source != "unsure":
            human_source = str(source).replace("_", " ")
            body_lines.append(
                f"I have maintained a savings/current bank account and the cash deposited "
                f"during the above said assessment year is from {human_source}. "
                "Copy of Bank Statement and Cash Ledger is enclosed."
            )

        elif req_cat == "credits_debits" and sig_ans:
            text_val = explanation_fn(sig_ans) if explanation_fn else str(sig_ans)
            body_lines.append(
                f"The significant credits/debits appearing in my bank account pertain to "
                f"{text_val}. Copy of supporting ledgers and transaction statement is enclosed."
            )

        elif req_cat == "other_notice_request" and other_ans:
            text_val = other_fn(other_ans) if other_fn else str(other_ans)
            body_lines.append(
                f"{text_val} Supporting records are enclosed."
            )

        elif req_cat == "computation" or "computation" in req_title.lower():
            body_lines.append(
                "Copy of Computation of total income for the above said Assessment year is "
                "enclosed for your ready reference along with return acknowledgment."
            )

        elif (
            req_cat == "balance_sheet"
            or "balance sheet" in req_title.lower()
            or "financial statements" in req_title.lower()
        ):
            body_lines.append(
                "Copy of Comparative Complete Balance Sheet and Profit & Loss statement "
                "for the relevant assessment year is enclosed."
            )

        elif req_cat == "bank_statements" or "bank" in req_title.lower():
            body_lines.append(
                "Copy of Bank Statement(s) for the relevant assessment year is enclosed. "
                "All bank accounts maintained during the year have been disclosed."
            )

        elif req_cat == "tds_mismatch" or "tds" in req_title.lower() or "26as" in req_title.lower():
            body_lines.append(
                "Copy of Form 26AS / AIS and the relevant TDS certificates are enclosed "
                "for reconciliation with the return filed."
            )

        elif req_cat == "deductions_exemptions" or "deduction" in req_title.lower():
            body_lines.append(
                "The deductions and exemptions claimed in the return are supported by the "
                "records enclosed herewith."
            )

        else:
            # Generic: use choice prose if available, or ask taxpayer to fill in
            prose = _choice_to_prose(choice_id) or ans_choice_raw or ""
            if prose:
                body_lines.append(prose)
            else:
                body_lines.append(
                    "[Please describe your response to this requisition before submission.]"
                )

        # Compose the numbered point
        lines.append(f"{index}. {req_title}")
        for bl in body_lines:
            lines.append(f"   {bl}")
        lines.append(f"   {_annexure_label(annexure_counter)}")
        lines.append("")

        annexure_list.append(
            f"Annexure {annexure_counter}: {_annexure_name_for(req_title, req_cat, annexure_counter)}"
        )
        annexure_counter += 1

    # ------------------------------------------------------------ closing
    lines.extend([
        "The above submissions along with the supporting annexures are true and correct "
        "to the best of my knowledge and records. If any further clarification or "
        "document is required, the same shall be provided upon requisition.",
        "",
        "Kindly place the above explanation and enclosed documents on record and "
        "conclude the proceedings.",
        "",
        "Thanking you,",
        "",
        "Yours faithfully,",
        "",
        f"({name})",
        "Taxpayer / Authorized Signatory",
        "",
    ])

    # ----------------------------------------------- list of enclosures
    if annexure_list:
        lines.append("List of Enclosures / Annexures:")
        for annex in annexure_list:
            lines.append(f"- {annex}")
        lines.append("")

    # ---------------------------------------------------- boundary note
    lines.append(
        "Note: This draft is structured based on the taxpayer's stated position and "
        "records. Tax Mitra has not verified taxpayer facts and has not submitted "
        "anything to the Income Tax Department. The taxpayer should review and verify "
        "all information before submitting through the official e-Filing portal."
    )

    if due_date:
        lines.append(f"Response deadline shown on the notice: {due_date}.")

    return "\n".join(lines)

"""Authentic Income Tax response letter generator modeled after real taxpayer submissions."""

from __future__ import annotations

from datetime import date
from typing import Any


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
    """Format an authentic, professional Income Tax reply letter matching actual CA/taxpayer submissions."""
    section = notice.get("section") or "142(1)"
    official_ref = notice.get("official_reference") or notice.get("id") or "DIN-DEMO"
    assessment_year = notice.get("assessment_year") or "2024-25"
    issue_date = notice.get("issue_date") or date.today().strftime("%d/%m/%Y")
    today_str = date.today().strftime("%d/%m/%Y")
    name = taxpayer_name or notice.get("taxpayer_name") or "Taxpayer"
    pan_no = pan or notice.get("pan") or "[PAN as per e-Filing profile]"

    lines: list[str] = [
        f"Date: - {today_str}",
        "",
        "To",
        "Assessment Unit / Verification Unit / Technical Unit / Review Unit",
        "Income Tax Department",
        "",
        "Dear Sir/Madam,",
        "",
        f"Ref:  {name}",
        f"      PAN: {pan_no}",
        f"      ASSESSMENT YEAR: {assessment_year}",
        f"      DIN: {official_ref}",
        f"Sub: Reply in accordance with Notice under Section {section} of the I. T. Act",
        "",
        "With reference to the above subject, I wish to state as under:",
        "",
        f"I have received your notice u/s {section} of I.T. Act 1961 dated {issue_date}. "
        "In response to the questionnaire as per the Notice, I am submitting the following details:",
        "",
    ]

    annexure_counter = 1
    annexure_list: list[str] = []

    source = answers.get("cash_deposit_source")
    sig_ans = answers.get("significant_transaction_explanation")
    other_ans = answers.get("other_request_details")

    # Numbered points mapped to notice requests
    for index, request in enumerate(requests, start=1):
        req_title = getattr(request, "response_section", "") or getattr(request, "category", "") or f"Requisition {index}"
        req_text = getattr(request, "original_text", "") or req_title
        req_cat = getattr(request, "category", "")

        lines.append(f"{index}. {req_title}")
        lines.append(f"Department request: {req_text}")

        if req_cat == "cash_deposits" and source and source != "unsure":
            human_source = str(source).replace("_", " ")
            lines.append(f"Taxpayer information provided: The stated source is {human_source}.")
            lines.append("Copy of Bank statement and Cash Ledger is enclosed.")
            lines.append(f"(As per Annexure - {annexure_counter})")
            annexure_list.append(f"Annexure {annexure_counter}: Bank statement and Cash Ledger copy")
            annexure_counter += 1

        elif req_cat == "credits_debits" and sig_ans:
            text_val = explanation_fn(sig_ans) if explanation_fn else str(sig_ans)
            lines.append(f"Taxpayer information provided: {text_val}")
            lines.append("Copy of supporting ledgers and transaction statement is enclosed.")
            lines.append(f"(As per Annexure - {annexure_counter})")
            annexure_list.append(f"Annexure {annexure_counter}: Statement of transactions and supporting ledgers")
            annexure_counter += 1

        elif req_cat == "other_notice_request" and other_ans:
            text_val = other_fn(other_ans) if other_fn else str(other_ans)
            lines.append(f"Taxpayer information provided: {text_val}")
            lines.append("Supporting records are enclosed.")
            lines.append(f"(As per Annexure - {annexure_counter})")
            annexure_list.append(f"Annexure {annexure_counter}: Supporting records for {req_title}")
            annexure_counter += 1

        elif req_cat == "computation" or "computation" in req_title.lower():
            lines.append("Copy of Computation of total income for the above said Assessment year is enclosed for your ready reference along with return acknowledgment.")
            lines.append(f"(As per Annexure - {annexure_counter})")
            annexure_list.append(f"Annexure {annexure_counter}: Copy of Computation of total income & return acknowledgment")
            annexure_counter += 1

        elif req_cat == "balance_sheet" or "balance sheet" in req_title.lower() or "financial statements" in req_title.lower():
            lines.append("Copy of Comparative Complete Balance sheet and Profit & Loss statement for the relevant assessment year is enclosed.")
            lines.append(f"(As per Annexure - {annexure_counter})")
            annexure_list.append(f"Annexure {annexure_counter}: Copy of Complete Balance sheet and Profit & Loss statement")
            annexure_counter += 1

        else:
            lines.append("The taxpayer should attach the relevant records identified in the evidence checklist and verify this section before submission.")
            lines.append(f"(As per Annexure - {annexure_counter})")
            annexure_list.append(f"Annexure {annexure_counter}: Supporting records for {req_title}")
            annexure_counter += 1

        lines.append("")

    # General affirmations
    lines.extend([
        "General Declarations:",
        "- During the above said assessment year no purchase or sale of immovable Property was done; hence, computation of capital gain on sale of property is not applicable.",
        "- All bank accounts maintained by the taxpayer during the relevant previous year have been fully disclosed.",
        "",
        "The above submissions along with the supporting annexures are true and correct to the best of my knowledge and records. "
        "If any further clarification or document is required, the same shall be provided upon requisition.",
        "",
        "Kindly place the above explanation and enclosed documents on record and conclude the proceedings.",
        "",
        "Thanking you,",
        "",
        "Yours faithfully,",
        "",
        f"({name})",
        "Taxpayer / Authorized Signatory",
        "",
    ])

    if annexure_list:
        lines.append("List of Enclosures / Annexures:")
        for annex in annexure_list:
            lines.append(f"- {annex}")
        lines.append("")

    lines.append(
        "Note: This response draft is structured based on the taxpayer's stated position and records. "
        "Tax Mitra has not verified taxpayer facts and has not submitted anything to the Income Tax Department. "
        "The taxpayer should review and verify all information before submitting through the official e-Filing portal."
    )

    if due_date:
        lines.append(f"Response deadline shown on the notice: {due_date}.")

    return "\n".join(lines)

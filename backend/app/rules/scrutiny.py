"""Deterministic Section 142(1) scrutiny-notice workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.extraction.notices import ExtractedRequest, confirmed_requests, extract_notice_requests
from app.rules.decision_trees import Option, YES_NO_UNSURE_IDS
from app.rules.refusal import OFFICIAL_EFILING_URL, OFFICIAL_HELP_URL

Text = dict[str, str]

ANSWER_YES = "yes"
ANSWER_NO = "no"
ANSWER_UNSURE = "unsure"


@dataclass(frozen=True)
class ScrutinyRequest:
    id: str
    original_text: str
    plain_language_explanation: Text
    why_required: Text
    required_evidence: tuple[Text, ...]
    response_section: str
    citations: tuple[str, ...]


@dataclass(frozen=True)
class ScrutinyQuestion:
    id: str
    request_id: str
    text: Text
    help: Text
    options: tuple[Option, ...]


_OPTIONS = (
    Option("yes", {"en": "Yes", "hi": "हाँ"}),
    Option("no", {"en": "No", "hi": "नहीं"}),
    Option("unsure", {"en": "I'm not sure", "hi": "मुझे पक्का नहीं है"}),
)


_REQUEST_LIBRARY: dict[str, dict[str, Any]] = {
    "req_computation_income": {
        "plain": {
            "en": "The officer wants a clear calculation showing how total income was arrived at for the assessment year.",
            "hi": "अधिकारी यह देखना चाहते हैं कि आकलन वर्ष के लिए कुल आय की गणना कैसे की गई।",
        },
        "why": {
            "en": "A computation connects the return, books, and supporting records into one verifiable summary.",
            "hi": "कुल आय की गणना रिटर्न, बही-खातों और सहायक रिकॉर्ड को एक सत्यापन योग्य सारांश में जोड़ती है।",
        },
        "evidence": (
            {"en": "Computation sheet by income head", "hi": "आय शीर्षों के अनुसार गणना पत्रक"},
            {"en": "Filed return acknowledgement and schedules", "hi": "दाखिल रिटर्न की पावती और अनुसूचियां"},
        ),
    },
    "req_balance_sheet": {
        "plain": {
            "en": "The officer wants a statement of assets, liabilities, and capital as at year end.",
            "hi": "अधिकारी वर्ष के अंत की परिसंपत्तियों, देनदारियों और पूंजी का विवरण चाहते हैं।",
        },
        "why": {
            "en": "The balance sheet helps reconcile capital, loans, bank balances, and business position with the return.",
            "hi": "बैलेंस शीट पूंजी, ऋण, बैंक शेष और व्यवसाय की स्थिति को रिटर्न से मिलाने में मदद करती है।",
        },
        "evidence": (
            {"en": "Balance sheet as at 31 March", "hi": "31 मार्च की बैलेंस शीट"},
            {"en": "Supporting schedules for loans, capital, assets, and liabilities", "hi": "ऋण, पूंजी, परिसंपत्ति और देनदारी की सहायक अनुसूचियां"},
        ),
    },
    "req_profit_loss": {
        "plain": {
            "en": "The officer wants the business income statement for the financial year.",
            "hi": "अधिकारी वित्त वर्ष का व्यवसाय आय-विवरण चाहते हैं।",
        },
        "why": {
            "en": "The Profit and Loss account supports turnover, expenses, gross profit, and net profit reported in the return.",
            "hi": "लाभ-हानि खाता रिटर्न में बताए गए टर्नओवर, खर्च, सकल लाभ और शुद्ध लाभ का समर्थन करता है।",
        },
        "evidence": (
            {"en": "Profit and Loss account for the financial year", "hi": "वित्त वर्ष का लाभ-हानि खाता"},
            {"en": "Ledger summaries for major income and expense heads", "hi": "मुख्य आय और खर्च शीर्षों के लेजर सारांश"},
        ),
    },
    "req_bank_statements": {
        "plain": {
            "en": "The officer wants complete bank statements for accounts used in business transactions.",
            "hi": "अधिकारी व्यवसाय लेनदेन में उपयोग किए गए खातों के पूरे बैंक विवरण चाहते हैं।",
        },
        "why": {
            "en": "Bank statements let the officer match reported turnover, receipts, payments, and balances against actual account activity.",
            "hi": "बैंक विवरण से अधिकारी टर्नओवर, प्राप्तियां, भुगतान और शेष को वास्तविक खाते की गतिविधि से मिला सकते हैं।",
        },
        "evidence": (
            {"en": "Full bank statements for all relevant accounts", "hi": "सभी संबंधित खातों के पूर्ण बैंक विवरण"},
            {"en": "Account list identifying business and personal accounts used for business", "hi": "व्यवसाय में उपयोग हुए व्यवसायिक और व्यक्तिगत खातों की सूची"},
        ),
    },
    "req_cash_deposits": {
        "plain": {
            "en": "The officer wants a source-wise explanation for cash deposited into bank accounts.",
            "hi": "अधिकारी बैंक खातों में जमा नकद का स्रोत-वार स्पष्टीकरण चाहते हैं।",
        },
        "why": {
            "en": "Cash deposits are checked to understand whether they match recorded sales, withdrawals, capital, loans, or other explained sources.",
            "hi": "नकद जमा यह समझने के लिए जांचे जाते हैं कि वे बिक्री, निकासी, पूंजी, ऋण या अन्य स्पष्ट स्रोतों से मेल खाते हैं या नहीं।",
        },
        "evidence": (
            {"en": "Cash book or cash summary", "hi": "कैश बुक या नकद सारांश"},
            {"en": "Source-wise explanation for each material cash deposit", "hi": "हर महत्वपूर्ण नकद जमा का स्रोत-वार स्पष्टीकरण"},
            {"en": "Supporting invoices, withdrawal records, loan confirmations, or capital records", "hi": "इनवॉइस, निकासी रिकॉर्ड, ऋण पुष्टि या पूंजी रिकॉर्ड"},
        ),
    },
    "req_significant_transactions": {
        "plain": {
            "en": "The officer wants explanations and evidence for large or unusual credits and debits.",
            "hi": "अधिकारी बड़े या असामान्य क्रेडिट और डेबिट का स्पष्टीकरण और प्रमाण चाहते हैं।",
        },
        "why": {
            "en": "Significant transactions may affect income, expenses, loans, investments, or unexplained money, so each material item needs a record-backed explanation.",
            "hi": "महत्वपूर्ण लेनदेन आय, खर्च, ऋण, निवेश या अस्पष्टीकृत धन को प्रभावित कर सकते हैं, इसलिए हर महत्वपूर्ण मद का रिकॉर्ड-आधारित स्पष्टीकरण चाहिए।",
        },
        "evidence": (
            {"en": "Transaction-wise explanation for significant credits and debits", "hi": "महत्वपूर्ण क्रेडिट और डेबिट का लेनदेन-वार स्पष्टीकरण"},
            {"en": "Invoices, agreements, confirmations, receipts, or ledger extracts", "hi": "इनवॉइस, अनुबंध, पुष्टि, रसीदें या लेजर अंश"},
        ),
    },
}


def is_scrutiny_notice(notice: dict) -> bool:
    return str(notice.get("section", "")).strip().lower().replace(" ", "").startswith("142(1)")


def build_scrutiny_requests(notice: dict, extraction_confirmed: bool = True) -> tuple[ScrutinyRequest, ...]:
    extracted = extract_notice_requests(notice)
    requests = confirmed_requests(extracted, extraction_confirmed)
    out: list[ScrutinyRequest] = []
    for item in requests:
        out.append(_enrich_request(item))
    return tuple(out)


def _enrich_request(item: ExtractedRequest) -> ScrutinyRequest:
    configured = _REQUEST_LIBRARY.get(item.id)
    if configured is None:
        raise KeyError(f"Unknown scrutiny request id: {item.id}")
    return ScrutinyRequest(
        id=item.id,
        original_text=item.original_text,
        plain_language_explanation=configured["plain"],
        why_required=configured["why"],
        required_evidence=tuple(configured["evidence"]),
        response_section=item.response_section,
        citations=item.citations,
    )


def scrutiny_questions(requests: tuple[ScrutinyRequest, ...]) -> tuple[ScrutinyQuestion, ...]:
    return tuple(
        ScrutinyQuestion(
            id=f"evidence_{request.id}",
            request_id=request.id,
            text={
                "en": f"Do you have the documents or explanation for: {request.response_section}?",
                "hi": f"क्या आपके पास इसके लिए दस्तावेज़ या स्पष्टीकरण है: {request.response_section}?",
            },
            help={
                "en": "Answer only from records you actually have. Choose 'I'm not sure' if you need to verify.",
                "hi": "केवल अपने वास्तविक रिकॉर्ड के आधार पर उत्तर दें। जांच करनी हो तो 'मुझे पक्का नहीं है' चुनें।",
            },
            options=_OPTIONS,
        )
        for request in requests
    )


def questions_payload(questions: tuple[ScrutinyQuestion, ...], locale: str) -> list[dict]:
    return [
        {
            "id": question.id,
            "request_id": question.request_id,
            "text": question.text.get(locale, question.text["en"]),
            "help": question.help.get(locale, question.help["en"]),
            "options": [
                {"id": option.id, "label": option.label.get(locale, option.label["en"])}
                for option in question.options
            ],
        }
        for question in questions
    ]


def request_payload(requests: tuple[ScrutinyRequest, ...], citations_by_id: dict[str, list[dict]]) -> list[dict]:
    return [
        {
            "id": request.id,
            "original_text": request.original_text,
            "plain_language_explanation": request.plain_language_explanation,
            "why_required": request.why_required,
            "required_evidence": list(request.required_evidence),
            "response_section": request.response_section,
            "citations": citations_by_id.get(request.id, []),
        }
        for request in requests
    ]


def validate_answers(questions: tuple[ScrutinyQuestion, ...], answers: dict[str, str]) -> None:
    expected = {question.id for question in questions}
    missing = expected - set(answers)
    if missing:
        raise ValueError(f"Missing answers for: {sorted(missing)}")
    invalid = {key: value for key, value in answers.items() if key in expected and value not in YES_NO_UNSURE_IDS}
    if invalid:
        first_key = next(iter(invalid))
        raise ValueError(f"Invalid answer '{invalid[first_key]}' for {first_key}")


def resolve_scrutiny(notice: dict, answers: dict[str, str], extraction_confirmed: bool = True) -> dict:
    requests = build_scrutiny_requests(notice, extraction_confirmed=extraction_confirmed)
    if not requests:
        return insufficient_information_refusal("Extraction has not been confirmed or no annexure requests were found.")

    questions = scrutiny_questions(requests)
    try:
        validate_answers(questions, answers)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    statuses = {question.request_id: answers[question.id] for question in questions}
    if any(value == ANSWER_UNSURE for value in statuses.values()):
        path = "needs_review"
    elif any(value == ANSWER_NO for value in statuses.values()):
        path = "needs_evidence"
    else:
        path = "ready_to_respond"

    due = notice.get("response_due_date")
    return {
        "supported": True,
        "category": "scrutiny_142_1",
        "path": {
            "path_id": path,
            "headline": _headline(path),
            "professional_help_recommended": path == "needs_review",
        },
        "checklist": _checklist(requests, statuses),
        "draft": _draft(notice, requests, statuses, due),
        "deadline": {
            "due_date": due,
            "status": "action_required" if due else "no_deadline",
        },
        "official_step": {
            "label": {
                "en": "Upload your response and evidence on the official e-Filing portal",
                "hi": "अपना उत्तर और प्रमाण आधिकारिक e-Filing पोर्टल पर अपलोड करें",
            },
            "url": OFFICIAL_EFILING_URL,
            "boundary": {
                "en": "Tax Mitra has not submitted your response. No documents or facts have been sent to the Income Tax Department.",
                "hi": "Tax Mitra ने आपका उत्तर जमा नहीं किया है। कोई दस्तावेज़ या तथ्य आयकर विभाग को नहीं भेजे गए हैं।",
            },
        },
    }


def insufficient_information_refusal(reason: str) -> dict:
    return {
        "supported": False,
        "category": "scrutiny_142_1",
        "headline": {
            "en": "We need a confirmed list of requested items before guiding this notice",
            "hi": "इस नोटिस में मार्गदर्शन से पहले मांगी गई मदों की पुष्टि सूची चाहिए",
        },
        "why": {
            "en": reason,
            "hi": "नोटिस की जानकारी पर्याप्त रूप से पुष्टि नहीं हुई है, इसलिए सुरक्षित मार्गदर्शन संभव नहीं है।",
        },
        "suggestion": {
            "en": "Confirm the extracted annexure requests from the notice PDF, or consult a tax professional before responding.",
            "hi": "नोटिस PDF से निकाली गई अनुबंध मदों की पुष्टि करें, या उत्तर देने से पहले कर-विशेषज्ञ से सलाह लें।",
        },
        "official_links": [
            {"label": {"en": "Official Income Tax e-Filing portal", "hi": "आयकर e-Filing पोर्टल"}, "url": OFFICIAL_EFILING_URL},
            {"label": {"en": "e-Filing help centre", "hi": "e-Filing सहायता केंद्र"}, "url": OFFICIAL_HELP_URL},
        ],
    }


def _headline(path: str) -> Text:
    if path == "ready_to_respond":
        return {
            "en": "You appear ready to prepare a response package",
            "hi": "आप उत्तर पैकेज तैयार करने के लिए तैयार लगते हैं",
        }
    if path == "needs_evidence":
        return {
            "en": "Collect the missing evidence before submitting",
            "hi": "जमा करने से पहले छूटे हुए प्रमाण इकट्ठा करें",
        }
    return {
        "en": "Some items need verification or professional review",
        "hi": "कुछ मदों की जांच या विशेषज्ञ समीक्षा चाहिए",
    }


def _checklist(requests: tuple[ScrutinyRequest, ...], statuses: dict[str, str]) -> list[dict]:
    items: list[dict] = []
    for request in requests:
        answer = statuses[request.id]
        prefix = {
            ANSWER_YES: {"en": "Attach", "hi": "संलग्न करें"},
            ANSWER_NO: {"en": "Obtain", "hi": "प्राप्त करें"},
            ANSWER_UNSURE: {"en": "Verify", "hi": "जांच करें"},
        }[answer]
        items.append(
            {
                "id": f"check_{request.id}",
                "request_id": request.id,
                "status": answer,
                "title": {
                    "en": f"{prefix['en']}: {request.response_section}",
                    "hi": f"{prefix['hi']}: {request.response_section}",
                },
                "required_evidence": list(request.required_evidence),
                "why_needed": request.why_required,
            }
        )
    return items


def _draft(notice: dict, requests: tuple[ScrutinyRequest, ...], statuses: dict[str, str], due: str | None) -> str:
    lines = [
        f"Subject: Response to notice under section {notice.get('section', '142(1)')} - {notice.get('official_reference', '')} (Assessment Year {notice.get('assessment_year', '')})",
        "",
        "Respected Sir/Madam,",
        "",
        f"I refer to the notice dated {notice.get('issue_date', '')} requiring information and documents for Assessment Year {notice.get('assessment_year', '')}.",
        "This draft is structured request-wise and should be reviewed against the taxpayer's actual records before upload.",
        "",
    ]
    for index, request in enumerate(requests, start=1):
        answer = statuses[request.id]
        lines.extend([f"{index}. {request.response_section}", f"Original request: {request.original_text}"])
        if answer == ANSWER_YES:
            evidence = "; ".join(item["en"] for item in request.required_evidence)
            lines.append(f"Response: The relevant records are available and should be enclosed: {evidence}.")
        elif answer == ANSWER_NO:
            lines.append("Response: The relevant records are being obtained. Do not submit this section as complete until the evidence is available.")
        else:
            lines.append("Response: The item needs verification from records. Consider professional review before taking a final position.")
        lines.append("")
    if due:
        lines.append(f"Response deadline shown on the synthetic notice: {due}.")
    lines.extend(
        [
            "Tax Mitra has not verified taxpayer facts and has not submitted anything to the Income Tax Department.",
            "",
            "Sincerely,",
            "Taxpayer",
            f"Date: {date.today().isoformat()}",
        ]
    )
    return "\n".join(lines)

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
    confidence: float = 1.0
    warnings: tuple[str, ...] = ()
    grounding: dict | None = None
    page_number: int | None = None
    source_location: str | None = None
    category: str = "other_notice_request"
    clarifying_questions: tuple[dict, ...] = ()
    status: str = "not_started"


@dataclass(frozen=True)
class ScrutinyQuestion:
    id: str
    request_id: str
    text: Text
    help: Text
    options: tuple[Option, ...]


_OPTIONS = (
    Option("yes", {"en": "I have it", "hi": "मेरे पास है"}),
    Option("no", {"en": "I don't have it", "hi": "मेरे पास नहीं है"}),
    Option("unsure", {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}),
)


_REQUEST_LIBRARY: dict[str, dict[str, Any]] = {
    "req_computation_income": {
        "plain": {
            "en": "The Assessing Officer has requested the computation of total income. Plain meaning: The calculation used to arrive at the income on which your tax is determined.",
            "hi": "आकलन अधिकारी ने कुल आय की गणना (computation) मांगी है। आसान अर्थ: वह गणना जिससे आपकी कुल कर-योग्य आय और देय कर निर्धारित होता है।",
        },
        "why": {
            "en": "The computation lets the Department reconcile the return of income with your books and supporting documents.",
            "hi": "कुल आय की गणना रिटर्न, बही-खातों और सहायक रिकॉर्ड को एक सत्यापन योग्य सारांश में जोड़ती है।",
        },
        "evidence": (
            {"en": "Computation of total income by income head", "hi": "आय शीर्षों के अनुसार कुल आय की computation"},
            {"en": "Filed return acknowledgement and schedules", "hi": "दाखिल रिटर्न की पावती और अनुसूचियां"},
        ),
    },
    "req_balance_sheet": {
        "plain": {
            "en": "The Assessing Officer has requested the balance sheet. Plain meaning: Shows your financial position, including what you own and what you owe.",
            "hi": "आकलन अधिकारी ने बैलेंस शीट मांगी है। आसान अर्थ: आपकी वित्तीय स्थिति दिखाता है, जिसमें आपकी संपत्ति और देनदारियां शामिल हैं।",
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
            "en": "The Assessing Officer has requested the Profit and Loss Account. Plain meaning: Shows the income earned and expenses incurred during the relevant period.",
            "hi": "आकलन अधिकारी ने लाभ और हानि खाता (P&L) मांगा है। आसान अर्थ: संबंधित अवधि के दौरान अर्जित आय और किए गए खर्चों का विवरण दिखाता है।",
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
            "en": "The Assessing Officer has requested complete bank statements. Plain meaning: Official records from your bank showing all money coming in and going out during the year.",
            "hi": "आकलन अधिकारी ने बैंक विवरण मांगे हैं। आसान अर्थ: बैंक के आधिकारिक रिकॉर्ड जो वित्तीय वर्ष के दौरान खाते में आए और गए सभी पैसों को दिखाते हैं।",
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
            "en": "The Assessing Officer has requested an explanation of cash deposits. Plain meaning: Clear explanation and source documents showing where physical cash deposited into your bank came from.",
            "hi": "आकलन अधिकारी ने नकद जमा का स्पष्टीकरण मांगा है। आसान अर्थ: स्पष्टीकरण और रिकॉर्ड कि आपके बैंक खातों में जमा किया गया नकद कहाँ से आया।",
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
            "en": "The Assessing Officer has requested an explanation of significant transactions. Plain meaning: Explanations and supporting proof for unusually large receipts or payments in your accounts.",
            "hi": "आकलन अधिकारी ने महत्वपूर्ण लेन-देन का स्पष्टीकरण मांगा है। आसान अर्थ: आपके खातों में असामान्य रूप से बड़े लेन-देन या भुगतानों का स्पष्टीकरण और प्रमाण।",
        },
        "why": {
            "en": "Significant transactions may affect income, expenses, loans, investments, or unexplained money, so each material item needs a record-backed explanation.",
            "hi": "महत्वपूर्ण लेनदेन आय, खर्च, ऋण, निवेश या अस्पष्टीकृत धन को प्रभावित कर सकते हैं, इसलिए हर महत्वपूर्ण मद का रिकॉर्ड-आधारित स्पष्टीकरण चाहिए।",
        },
        "evidence": (
            {"en": "Transaction-wise explanation for significant credits and debits", "hi": "महत्वपूर्ण credits और debits का लेनदेन-वार स्पष्टीकरण"},
            {"en": "Invoices, agreements, confirmations, receipts, or ledger extracts", "hi": "इनवॉइस, अनुबंध, पुष्टि, रसीदें या लेजर अंश"},
        ),
    },
    # Additional request types for demo PDF items
    "req_ledger_extract": {
        "plain": {
            "en": "The Assessing Officer has requested a ledger extract showing professional receipts and the related invoices.",
            "hi": "आकलन अधिकारी ने professional receipts और उनसे जुड़े invoices दिखाने वाला ledger extract मांगा है।",
        },
        "why": {
            "en": "The ledger extract helps reconcile professional income reported in the return with the related invoices.",
            "hi": "ledger extract से रिटर्न में बताई गई professional income को संबंधित invoices से मिलाने में मदद मिलती है।",
        },
        "evidence": (
            {"en": "Ledger extract for professional receipts", "hi": "professional receipts का ledger extract"},
            {"en": "Supporting invoices for professional receipts", "hi": "professional receipts के supporting invoices"},
        ),
    },
    "req_high_value_transactions": {
        "plain": {
            "en": "The Assessing Officer has requested an explanation for high-value transactions appearing in AIS or SFT information.",
            "hi": "अधिकारी AIS / SFT में दिखाई देने वाले उच्च-मूल्य लेनदेन का स्पष्टीकरण चाहते हैं।",
        },
        "why": {
            "en": "High-value transactions in AIS/SFT may indicate income that needs explanation to match reported figures.",
            "hi": "AIS/SFT में उच्च-मूल्य लेनदेन रिपोर्ट किए गए आंकड़ों से मेल खाते हो सकते हैं, इसलिए स्पष्टीकरण चाहिए।",
        },
        "evidence": (
            {"en": "Explanation for each high-value transaction", "hi": "हर उच्च-मूल्य लेनदेन का स्पष्टीकरण"},
            {"en": "Supporting documents for the transactions", "hi": "लेनदेन के लिए सहायक दस्तावेज़"},
        ),
    },
    "req_tax_payments": {
        "plain": {
            "en": "The Assessing Officer has requested details of tax payments, including TDS, TCS, and challan numbers.",
            "hi": "अधिकारी कर भुगतान, TDS, TCS और चल्लन नंबर का विवरण चाहते हैं।",
        },
        "why": {
            "en": "Tax payment details help verify that advance tax and withheld taxes match the return figures.",
            "hi": "कर भुगतान का विवरण यह सत्यापित करने में मदद करता है कि अग्रिम कर और काटे गए कर रिटर्न आंकड़ों से मेल खाते हैं।",
        },
        "evidence": (
            {"en": "Challan copies for tax payments", "hi": "कर भुगतान के चालान की प्रतियां"},
            {"en": "Form 26AS / AIS statement showing TDS/TCS", "hi": "TDS/TCS दिखाने वाला Form 26AS / AIS statement"},
        ),
    },
    "req_evidence": {
        "plain": {
            "en": "The Assessing Officer has requested any other supporting documents relied on for the return of income.",
            "hi": "अधिकारी रिटर्न के समर्थन में भरोसे किए गए किसी भी अन्य प्रमाण चाहते हैं।",
        },
        "why": {
            "en": "Additional evidence supports the accuracy and completeness of the filed return.",
            "hi": "अतिरिक्त प्रमाण दाखिल किए गए रिटर्न की सटीकता और पूर्णता का समर्थन करते हैं।",
        },
        "evidence": (
            {"en": "Any supporting documents referenced in the return", "hi": "रिटर्न में संदर्भित किसी भी सहायक दस्तावेज़"},
            {"en": "Records that support claimed deductions or exemptions", "hi": "दावा की गई कटौती या छूट का समर्थन करने वाले रिकॉर्ड"},
        ),
    },
}


_GENERIC_REQUEST = {
    "plain": {
        "en": "The notice requests the item shown below. Tax Mitra does not decide whether the request applies to your facts; check the notice and your records.",
        "hi": "नोटिस में नीचे दी गई जानकारी या दस्तावेज़ मांगा गया है। Tax Mitra यह तय नहीं करता कि यह अनुरोध आपके मामले में लागू है; नोटिस और अपने रिकॉर्ड देखें।",
    },
    "why": {
        "en": "Section 142(1) permits an Assessing Officer to require accounts, documents, or verified written information. This explanation does not add a legal requirement beyond the notice.",
        "hi": "धारा 142(1) के तहत आकलन अधिकारी खाते, दस्तावेज या सत्यापित लिखित जानकारी मांग सकते हैं। यह स्पष्टीकरण नोटिस से आगे कोई कानूनी आवश्यकता नहीं जोड़ता।",
    },
    "evidence": (),
}
_REQUEST_LIBRARY["req_notice_document"] = _GENERIC_REQUEST
_REQUEST_LIBRARY["req_deductions_exemptions"] = {
    "plain": {
        "en": "The Assessing Officer has requested records supporting the deductions or exemptions claimed in the return. In simple terms, provide the documents that support each claim.",
        "hi": "आकलन अधिकारी ने return में claim की गई deductions या exemptions के समर्थन में रिकॉर्ड मांगे हैं। आसान भाषा में, हर claim के समर्थन वाले दस्तावेज़ दें।",
    },
    "why": {
        "en": "These records allow the Department to verify the eligibility and amount of each deduction or exemption claimed.",
        "hi": "इन रिकॉर्ड से विभाग हर deduction या exemption की पात्रता और claim की गई राशि की जांच कर सकता है।",
    },
    "evidence": (
        {"en": "Evidence supporting each deduction or exemption claimed", "hi": "हर claim की गई deduction या exemption का supporting evidence"},
        {"en": "Relevant certificates, receipts, payment records, or policy documents", "hi": "संबंधित certificates, receipts, payment records या policy documents"},
    ),
}

_REQUEST_CATEGORIES = {
    "req_computation_income": "income_computation",
    "req_balance_sheet": "balance_sheet",
    "req_profit_loss": "profit_loss_statement",
    "req_bank_statements": "bank_statements",
    "req_cash_deposits": "cash_deposits",
    "req_significant_transactions": "credits_debits",
    "req_deductions_exemptions": "deductions_exemptions",
    "req_notice_document": "other_notice_request",
}

_REQUEST_QUESTIONS = {
    "req_computation_income": {"en": "Do you have the computation of total income for this Assessment Year?", "hi": "क्या आपके पास इस आकलन वर्ष की कुल आय की computation है?"},
    "req_balance_sheet": {"en": "Do you have the balance sheet for the period named in the notice?", "hi": "क्या आपके पास नोटिस में बताए गए समय की balance sheet है?"},
    "req_profit_loss": {"en": "Do you have the Profit and Loss Account for the Financial Year named in the notice?", "hi": "क्या आपके पास नोटिस में बताए गए वित्त वर्ष का Profit and Loss Account है?"},
    "req_bank_statements": {"en": "Can you obtain the complete bank statements requested in the notice?", "hi": "क्या आप नोटिस में मांगे गए पूरे bank statements प्राप्त कर सकते हैं?"},
    "req_cash_deposits": {"en": "Can you identify the source of each relevant cash deposit?", "hi": "क्या आप संबंधित cash deposits के स्रोत की पहचान कर सकते हैं?"},
    "req_significant_transactions": {"en": "Can you explain the significant credits and debits using your records?", "hi": "क्या आप अपने रिकॉर्ड से महत्वपूर्ण credits और debits समझा सकते हैं?"},
    "req_deductions_exemptions": {"en": "Do you have records supporting the deductions or exemptions claimed in the return?", "hi": "क्या आपके पास return में claim की गई deductions या exemptions के supporting records हैं?"},
    "req_notice_document": {"en": "Do you have records that address this specific request in the notice?", "hi": "क्या आपके पास नोटिस के इस विशेष अनुरोध से संबंधित रिकॉर्ड हैं?"},
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
    configured = _REQUEST_LIBRARY.get(item.classification_id or item.id)
    if configured is None:
        raise KeyError(f"Unknown scrutiny request id: {item.id}")
    citations = tuple(dict.fromkeys((*item.citations, "sec-142-0001")))
    return ScrutinyRequest(
        id=item.id,
        original_text=item.original_text,
        plain_language_explanation=configured["plain"],
        why_required=configured["why"],
        required_evidence=tuple(configured["evidence"]),
        response_section=item.response_section,
        citations=citations,
        confidence=float(getattr(item, "confidence", 1.0)),
        warnings=tuple(getattr(item, "warnings", ())),
        grounding=getattr(item, "grounding", None),
        page_number=getattr(item, "page_number", None),
        source_location=getattr(item, "source_location", None),
        category=getattr(item, "category", None) or _REQUEST_CATEGORIES.get(item.classification_id or item.id, "other_notice_request"),
        clarifying_questions=getattr(item, "clarifying_questions", ()) or ({"id": f"has_{item.id}", "text": _REQUEST_QUESTIONS.get(item.classification_id or item.id, _REQUEST_QUESTIONS["req_notice_document"])},),
        status=getattr(item, "status", "not_started"),
    )


def scrutiny_questions(requests: tuple[ScrutinyRequest, ...]) -> tuple[ScrutinyQuestion, ...]:
    return tuple(
        ScrutinyQuestion(
            id=f"evidence_{request.id}",
            request_id=request.id,
            text={
                "en": f"Does the Department's request match your records for: {request.response_section}?",
                "hi": f"क्या विभाग का अनुरोध आपके रिकॉर्ड से मेल खाता है: {request.response_section}?",
            },
            help={
                "en": "Check the Department's stated requirement against your actual records. 'Yes' means it matches, 'No' means it does not match, 'I'm not sure' means you need to verify.",
                "hi": "विभाग की बताई आवश्यकता को अपने वास्तविक रिकॉर्ड से मिलाइए। 'हाँ' का मतलब है यह मेल खाता है, 'नहीं' का मतलब है यह मेल नहीं खाता, 'मुझे पक्का नहीं है' का मतलब है आपको सत्यापित करने की जरूरत है।",
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
            "request_id": request.id,
            "classification_id": next((key for key, value in _REQUEST_LIBRARY.items() if value.get("plain") == request.plain_language_explanation), request.id),
            "original_text": request.original_text,
            "plain_language_explanation": request.plain_language_explanation,
            "why_required": request.why_required,
            "required_evidence": list(request.required_evidence),
            "what_department_is_asking": request.original_text,
            "expected_evidence": list(request.required_evidence),
            "response_section": request.response_section,
            "citations": citations_by_id.get(request.id, []),
            "confidence": request.confidence,
            "warnings": list(request.warnings),
            "grounding": request.grounding,
            "page_number": request.page_number,
            "page": request.page_number,
            "source_location": request.source_location,
            "category": request.category,
            "clarifying_questions": list(request.clarifying_questions),
            "status": request.status,
            "workflow_status": request.status,
            "sources": citations_by_id.get(request.id, []),
        }
        for request in requests
    ]


def validate_answers(questions: tuple[ScrutinyQuestion, ...], answers: dict[str, str]) -> None:
    expected = {question.id for question in questions}
    missing = expected - set(answers)
    if missing:
        raise ValueError(f"Missing answers for: {sorted(missing)}")
    unexpected = set(answers) - expected
    if unexpected:
        raise ValueError(f"Unexpected answers for: {sorted(unexpected)}")
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
            "en": "You confirmed the Department's requests match your records",
            "hi": "आपने पुष्टि की कि विभाग के अनुरोध आपके रिकॉर्ड से मेल खाते हैं",
        }
    if path == "needs_evidence":
        return {
            "en": "You identified discrepancies that need clarification",
            "hi": "आपने ऐसी विसंगतियां पहचानी हैं जिनका स्पष्टीकरण देना होगा",
        }
    return {
        "en": "You indicated some items need verification from your records",
        "hi": "आपने बताया कि कुछ मदों की आपके रिकॉर्ड से जांच चाहिए",
    }


def _checklist(requests: tuple[ScrutinyRequest, ...], statuses: dict[str, str]) -> list[dict]:
    items: list[dict] = []
    for request in requests:
        answer = statuses[request.id]
        prefix = {
            ANSWER_YES: {"en": "Attach matching records", "hi": "मेल खाते रिकॉर्ड संलग्न करें"},
            ANSWER_NO: {"en": "Clarify discrepancy", "hi": "विसंगति स्पष्ट करें"},
            ANSWER_UNSURE: {"en": "Verify from records", "hi": "रिकॉर्ड से सत्यापित करें"},
        }[answer]
        items.append(
            {
                "id": f"check_{request.id}",
                "request_id": request.id,
                "status": answer,
                "workflow_status": {ANSWER_YES: "ready_for_response", ANSWER_NO: "documents_needed", ANSWER_UNSURE: "need_information"}[answer],
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
    # Extract notice details
    section = notice.get('section', '142(1)')
    official_reference = notice.get('official_reference', '')
    assessment_year = notice.get('assessment_year', '')
    issue_date = notice.get('issue_date', '')
    
    # Determine appropriate recipient based on notice section
    if section.startswith('143'):
        recipient = "The Assessing Officer,\nCentralized Processing Centre - Demo,\nIncome Tax Department"
    elif section.startswith('142'):
        recipient = "The Assessing Officer,\nIncome Tax Department"
    else:
        recipient = "The Assessing Officer,\nIncome Tax Department"
    
    lines = [
        f"Date: {date.today().strftime('%d/%m/%Y')}",
        "",
        "To:",
        recipient,
        "",
        f"Subject: Response to notice under section {section} - {official_reference} (Assessment Year {assessment_year})",
        "",
        f"Reference: Notice under section {section} - {official_reference} dated {issue_date} - Assessment Year {assessment_year}",
        "",
        "Respected Sir/Madam,",
        "",
        "With reference to the above notice, I wish to state as under:",
        "",
    ]
    
    # Generate numbered response sections based on actual requests
    for index, request in enumerate(requests, start=1):
        answer = statuses[request.id]
        
        lines.append(f"{index}. {request.response_section}")
        
        if answer == ANSWER_YES:
            evidence = "; ".join(item["en"] for item in request.required_evidence)
            lines.append(f"With reference to the Department's request regarding {request.response_section}, I state that the information matches my records. The relevant documents are enclosed as follows:")
            lines.append(f"Supporting documents: {evidence}")
        elif answer == ANSWER_NO:
            lines.append(f"With reference to the Department's request regarding {request.response_section}, I state that the information does not match my records. The discrepancy is being clarified and supporting evidence will be provided once verified.")
            lines.append(f"Required clarification: The specific points of discrepancy are being reviewed and supporting documents will be submitted after verification.")
        else:
            lines.append(f"With reference to the Department's request regarding {request.response_section}, I state that the information requires verification from my records. I am currently reviewing the relevant documents before taking a final position.")
            lines.append(f"Action required: Verification of records is in progress. Consider professional review before finalizing the response.")
        
        lines.append("")
    
    # Add closing
    lines.extend([
        "Thanking you,",
        "",
        "Yours faithfully,",
        "[Taxpayer Name]",
        "",
        "Note: This response draft is structured based on the taxpayer's stated position and records. Tax Mitra has not verified taxpayer facts and has not submitted anything to the Income Tax Department. The taxpayer should review and verify all information before submitting through the official e-Filing portal.",
    ])
    
    if due:
        lines.append(f"Response deadline shown on the synthetic notice: {due}.")
    
    return "\n".join(lines)

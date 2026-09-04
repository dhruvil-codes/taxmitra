"""Deterministic, request-scoped evidence recommendations.

This layer describes possible evidence; it never stores taxpayer files. A
browser-first client can later attach local file handles or local-only
references to these stable recommendation ids without changing the rules API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DOCUMENT_STATUSES = {"have", "need_to_find", "dont_have", "not_sure"}


@dataclass(frozen=True)
class EvidenceRecommendation:
    request_id: str
    document_id: str
    document_name: dict[str, str]
    reason: dict[str, str]
    requirement_level: str
    source: tuple[str, ...]
    status: str = "not_sure"


_EVIDENCE: dict[str, tuple[tuple[str, dict[str, str], dict[str, str], str], ...]] = {
    "income_computation": (
        ("computation", {"en": "Computation of total income", "hi": "कुल आय की computation"}, {"en": "The notice asks for this calculation, which shows how the returned income was arrived at.", "hi": "नोटिस में यह गणना मांगी गई है, जिससे रिटर्न में बताई गई आय की गणना दिखाई जाती है।"}, "required"),
        ("return_acknowledgement", {"en": "Filed return acknowledgement and schedules", "hi": "दाखिल रिटर्न की पावती और अनुसूचियां"}, {"en": "This may help reconcile the computation with the filed return.", "hi": "इससे computation को दाखिल रिटर्न से मिलाने में मदद मिल सकती है।"}, "possibly_relevant"),
    ),
    "balance_sheet": (
        ("balance_sheet", {"en": "Balance sheet for the period named in the notice", "hi": "नोटिस में बताए समय की balance sheet"}, {"en": "The notice specifically asks for the balance sheet showing assets, liabilities and capital.", "hi": "नोटिस में परिसंपत्तियों, देनदारियों और पूंजी वाली balance sheet मांगी गई है।"}, "required"),
        ("balance_sheet_schedules", {"en": "Schedules for loans, capital, assets and liabilities", "hi": "ऋण, पूंजी, परिसंपत्ति और देनदारी की अनुसूचियां"}, {"en": "These may be relevant if they support figures in the balance sheet.", "hi": "यदि ये balance sheet के आंकड़ों का समर्थन करती हैं तो ये उपयोगी हो सकती हैं।"}, "possibly_relevant"),
    ),
    "profit_loss_statement": (
        ("profit_loss", {"en": "Profit and Loss Account for the named Financial Year", "hi": "बताए गए वित्त वर्ष का Profit and Loss Account"}, {"en": "The notice asks for this statement to show the income and expenses for the year.", "hi": "नोटिस में वर्ष की आय और खर्च दिखाने वाला यह विवरण मांगा गया है।"}, "required"),
        ("income_expense_ledger", {"en": "Ledger extracts for major income and expense heads", "hi": "मुख्य आय और खर्च शीर्षों के ledger extracts"}, {"en": "These may support the totals reported in the Profit and Loss Account.", "hi": "ये Profit and Loss Account में बताए कुल आंकड़ों का समर्थन कर सकते हैं।"}, "possibly_relevant"),
    ),
    "bank_statements": (
        ("bank_statements", {"en": "Complete bank statements for the accounts named in the notice", "hi": "नोटिस में बताए खातों के पूरे bank statements"}, {"en": "The notice asks for these records so transactions can be matched with the explanation.", "hi": "नोटिस में ये रिकॉर्ड इसलिए मांगे गए हैं ताकि लेनदेन को स्पष्टीकरण से मिलाया जा सके।"}, "required"),
        ("account_list", {"en": "List of relevant business and personal accounts", "hi": "संबंधित business और personal accounts की सूची"}, {"en": "This may help show which accounts were used for business transactions.", "hi": "इससे यह बताने में मदद मिल सकती है कि कौन से खाते business transactions में उपयोग हुए।"}, "possibly_relevant"),
    ),
    "cash_deposits": (
        ("cash_deposit_explanation", {"en": "Source-wise explanation of cash deposits", "hi": "cash deposits का source-wise explanation"}, {"en": "The department is asking you to explain the source of the cash deposits.", "hi": "विभाग cash deposits के स्रोत का स्पष्टीकरण मांग रहा है।"}, "required"),
        ("relevant_bank_statement", {"en": "Relevant bank statement", "hi": "संबंधित bank statement"}, {"en": "This may show the dates and amounts that the explanation covers.", "hi": "इससे स्पष्टीकरण में शामिल तारीखें और राशियां दिखाई जा सकती हैं।"}, "possibly_relevant"),
        ("cash_book", {"en": "Cash book, if maintained", "hi": "यदि रखी जाती हो तो cash book"}, {"en": "This may support recorded cash receipts, withdrawals or business deposits.", "hi": "यह दर्ज नकद प्राप्तियों, निकासी या business deposits का समर्थन कर सकती है।"}, "possibly_relevant"),
        ("cash_supporting_records", {"en": "Supporting invoices, receipts or withdrawal records", "hi": "supporting invoices, receipts या withdrawal records"}, {"en": "These may help support the stated source for a particular deposit.", "hi": "ये किसी खास deposit के बताए गए स्रोत का समर्थन कर सकते हैं।"}, "possibly_relevant"),
    ),
    "credits_debits": (
        ("transaction_explanation", {"en": "Transaction-wise explanation of significant credits and debits", "hi": "महत्वपूर्ण credits और debits का transaction-wise explanation"}, {"en": "The notice asks for an explanation of the significant entries identified in the statements.", "hi": "नोटिस में statements में पहचानी गई महत्वपूर्ण entries का explanation मांगा गया है।"}, "required"),
        ("transaction_supporting_records", {"en": "Invoices, agreements, confirmations, receipts or ledger extracts", "hi": "invoices, agreements, confirmations, receipts या ledger extracts"}, {"en": "These may support the nature and purpose of each significant transaction.", "hi": "ये हर महत्वपूर्ण transaction की प्रकृति और उद्देश्य का समर्थन कर सकते हैं।"}, "possibly_relevant"),
    ),
    "deductions_exemptions": (
        ("deduction_exemption_support", {"en": "Records supporting each deduction or exemption claimed", "hi": "claim की गई हर deduction या exemption के supporting records"}, {"en": "The notice asks for documents supporting the claims made in the return.", "hi": "नोटिस में return में किए गए claims के समर्थन में दस्तावेज़ मांगे गए हैं।"}, "required"),
        ("deduction_receipts_certificates", {"en": "Relevant receipts, certificates or payment records", "hi": "संबंधित receipts, certificates या payment records"}, {"en": "These may be relevant depending on the particular deduction or exemption claimed.", "hi": "दावा की गई deduction या exemption के अनुसार ये उपयोगी हो सकते हैं।"}, "possibly_relevant"),
    ),
}


def map_evidence(requests: tuple[Any, ...], statuses: dict[str, str] | None = None) -> list[dict]:
    """Return request-scoped recommendations without reading or storing files."""
    statuses = statuses or {}
    mapped: list[dict] = []
    for request in requests:
        entries = _EVIDENCE.get(request.category, (("request_records", {"en": "Records addressing the specific notice request", "hi": "नोटिस के विशेष अनुरोध से संबंधित रिकॉर्ड"}, {"en": "These may be relevant if the notice asks for supporting information not covered above.", "hi": "यदि नोटिस में ऊपर के अलावा सहायक जानकारी मांगी गई है तो ये उपयोगी हो सकते हैं।"}, "possibly_relevant"),))
        for document_id, name, reason, level in entries:
            key = f"{request.id}:{document_id}"
            mapped.append({
                "request_id": request.id,
                "document_id": key,
                "document_name": name,
                "reason": reason,
                "requirement_level": level,
                "required_or_possibly_relevant": level,
                "source": list(request.citations),
                "status": statuses.get(key, "not_sure"),
            })
    return mapped


def missing_evidence(recommendations: list[dict]) -> list[dict]:
    return [item for item in recommendations if item["status"] in {"need_to_find", "dont_have", "not_sure"}]

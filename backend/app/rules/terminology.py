"""Canonical Indian income-tax terminology used by user-facing copy.

Terms stay precise in English and use the Hindi wording taxpayers commonly
encounter on the Income Tax e-Filing portal. Explanations should introduce the
term first, then state what it means or what the taxpayer should check.
"""

from __future__ import annotations

TAX_TERMS = {
    "income_tax_department": {"en": "Income Tax Department", "hi": "आयकर विभाग"},
    "assessing_officer": {"en": "Assessing Officer", "hi": "आकलन अधिकारी"},
    "assessment_year": {"en": "Assessment Year", "hi": "आकलन वर्ष"},
    "return_of_income": {"en": "return of income", "hi": "आय का रिटर्न"},
    "information_mismatch": {"en": "information mismatch", "hi": "जानकारी में असंगति"},
    "proposed_adjustment": {"en": "proposed adjustment", "hi": "प्रस्तावित समायोजन"},
    "supporting_documents": {"en": "supporting documents", "hi": "सहायक दस्तावेज़"},
    "response_deadline": {"en": "response deadline", "hi": "उत्तर देने की अंतिम तिथि"},
    "e_filing_portal": {"en": "Income Tax e-Filing portal", "hi": "आयकर e-Filing पोर्टल"},
}


def term(key: str, locale: str = "en") -> str:
    """Return a canonical term, falling back to English for unknown locales."""
    return TAX_TERMS[key].get(locale, TAX_TERMS[key]["en"])


TERMINOLOGY_GUIDANCE = (
    "Use precise Indian income-tax terms: Assessment Year, return of income, "
    "information mismatch, proposed adjustment, supporting documents, AIS, "
    "Form 26AS, TDS, TCS, challan, Assessing Officer, and e-Filing portal. "
    "Introduce the term, then explain it in plain language. Separate what the "
    "notice says, what it means, and what the taxpayer should check or do. "
    "Do not call a proposed adjustment a final tax demand, and do not infer "
    "tax liability beyond the notice and supplied sources."
)

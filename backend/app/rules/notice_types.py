"""Compatibility facade for the universal notice workflow registry."""

from __future__ import annotations

from enum import Enum

from app.workflows.registry import WorkflowCapability, classify_extracted_notice, list_workflows


class NoticeCategory(str, Enum):
    INCOME_MISMATCH_143_1A = "income_mismatch_143_1a"
    SCRUTINY_142_1 = "scrutiny_142_1"
    DEFECTIVE_RETURN_139_9 = "defective_return_139_9"
    RECTIFICATION_TAX_CREDIT_MISMATCH = "rectification_tax_credit_mismatch"
    AO_NOTICE_CLARIFICATION = "ao_notice_clarification"
    INCOME_INTIMATION_143_1 = "income_intimation_143_1"
    SCRUTINY_INFORMATION_133_6 = "scrutiny_information_133_6"
    RECTIFICATION_154 = "rectification_154"
    TAX_CREDIT_TDS_MISMATCH = "tax_credit_tds_mismatch"
    DEMAND_ADJUSTMENT_245 = "demand_adjustment_245"
    OUTSTANDING_TAX_DEMAND = "outstanding_tax_demand"
    REFUND_COMMUNICATION = "refund_communication"
    REASSESSMENT_148 = "reassessment_148"
    REASSESSMENT_148A = "reassessment_148a"
    PENALTY_PROCEEDINGS = "penalty_proceedings"
    AUTHORITY_131 = "authority_131"
    COMPLIANCE_AIS = "compliance_ais"
    AUTHORITY_INFORMATION_REQUEST = "authority_information_request"
    UNKNOWN_INCOME_TAX_COMMUNICATION = "unknown_income_tax_communication"
    UNSUPPORTED = "unsupported"


# The categories the guided workflow can safely carry a citizen through.
# Scope is deliberate and small: if we cannot safely guide, we refuse.
SUPPORTED_CATEGORIES: frozenset[NoticeCategory] = frozenset(
    NoticeCategory(item["category"])
    for item in list_workflows()
    if item["supported"]
)


def _normalize(section: str | None) -> str:
    return (section or "").strip().lower().replace(" ", "")


def classify_notice(notice: dict) -> NoticeCategory:
    """Map extracted notice content to a category through the registry.

    This remains a total compatibility API for existing callers. Callers that
    need confidence and safe-stop metadata should use
    :func:`classify_extracted_notice` directly.
    """
    # Preserve the legacy section-only interpretation used by v0 callers;
    # universal callers use classify_extracted_notice and distinguish 143(1).
    if notice.get("section") == "143(1)" and not notice.get("official_text"):
        return NoticeCategory.INCOME_MISMATCH_143_1A
    result = classify_extracted_notice(notice)
    if result.category in {"reassessment_148", "unknown_income_tax_communication"}:
        return NoticeCategory.UNSUPPORTED
    try:
        return NoticeCategory(result.category)
    except ValueError:
        return NoticeCategory.UNSUPPORTED


def is_supported(category: NoticeCategory) -> bool:
    return category in SUPPORTED_CATEGORIES

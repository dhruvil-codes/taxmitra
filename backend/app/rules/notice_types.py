"""Notice classification — deterministic, based on structured notice metadata.

In this prototype, notices are synthetic and already carry structured fields
(section, issue_code). Classification is therefore a pure mapping. In a
production system this is where an extraction layer would feed structured
data in; the decision itself would remain rule-based, not model-based.
"""

from __future__ import annotations

from enum import Enum


class NoticeCategory(str, Enum):
    INCOME_MISMATCH_143_1A = "income_mismatch_143_1a"
    DEFECTIVE_RETURN_139_9 = "defective_return_139_9"
    UNSUPPORTED = "unsupported"


# The categories the guided workflow can safely carry a citizen through.
# Scope is deliberate and small: if we cannot safely guide, we refuse.
SUPPORTED_CATEGORIES: frozenset[NoticeCategory] = frozenset(
    {
        NoticeCategory.INCOME_MISMATCH_143_1A,
    }
)


def _normalize(section: str | None) -> str:
    return (section or "").strip().lower().replace(" ", "")


def classify_notice(notice: dict) -> NoticeCategory:
    """Map a notice's structured metadata to a category. Pure and total."""
    section = _normalize(notice.get("section"))
    if section.startswith("143(1)"):
        return NoticeCategory.INCOME_MISMATCH_143_1A
    if section.startswith("139(9)"):
        return NoticeCategory.DEFECTIVE_RETURN_139_9
    return NoticeCategory.UNSUPPORTED


def is_supported(category: NoticeCategory) -> bool:
    return category in SUPPORTED_CATEGORIES

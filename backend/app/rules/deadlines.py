"""Statutory response windows and deadline computation.

Pure functions: `today` is always injectable so tests are deterministic.
Day-3 manual verification pass must confirm each window against the
official source (tracked in docs/legal_verification_checklist.md).
"""

from __future__ import annotations

from datetime import date, timedelta

from app.rules.notice_types import NoticeCategory

# Response window per notice category, in days from the notice issue date.
# TODO-VERIFY(Day 3): confirm the 143(1)(a) e-campaign response window
# against the official e-Filing portal help pages before recording the demo.
RESPONSE_WINDOWS_DAYS: dict[NoticeCategory, int] = {
    NoticeCategory.INCOME_MISMATCH_143_1A: 30,
}

STATUS_ACTION_REQUIRED = "action_required"
STATUS_DUE_SOON = "due_soon"  # a week or less remains
STATUS_EXPIRED = "expired"

DUE_SOON_THRESHOLD_DAYS = 7


def compute_due_date(issue_date: date, category: NoticeCategory) -> date | None:
    """Due date = issue date + statutory window. None when no window is defined."""
    window = RESPONSE_WINDOWS_DAYS.get(category)
    if window is None:
        return None
    return issue_date + timedelta(days=window)


def days_remaining(due: date | None, today: date | None = None) -> int | None:
    if due is None:
        return None
    ref = today or date.today()
    return (due - ref).days


def deadline_status(due: date | None, today: date | None = None) -> str:
    """One of: action_required | due_soon | expired."""
    remaining = days_remaining(due, today)
    if remaining is None:
        return STATUS_ACTION_REQUIRED
    if remaining < 0:
        return STATUS_EXPIRED
    if remaining <= DUE_SOON_THRESHOLD_DAYS:
        return STATUS_DUE_SOON
    return STATUS_ACTION_REQUIRED

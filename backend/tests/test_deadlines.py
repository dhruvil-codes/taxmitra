from datetime import date

from app.rules.deadlines import (
    STATUS_ACTION_REQUIRED,
    STATUS_DUE_SOON,
    STATUS_EXPIRED,
    compute_due_date,
    days_remaining,
    deadline_status,
)
from app.rules.notice_types import NoticeCategory

TODAY = date(2026, 8, 24)


def test_due_date_is_issue_date_plus_window():
    assert compute_due_date(date(2026, 8, 13), NoticeCategory.INCOME_MISMATCH_143_1A) == date(2026, 9, 12)


def test_unsupported_category_has_no_window():
    assert compute_due_date(date(2026, 8, 13), NoticeCategory.UNSUPPORTED) is None


def test_days_remaining_counts_calendar_days():
    assert days_remaining(date(2026, 8, 25), TODAY) == 1
    assert days_remaining(date(2026, 8, 24), TODAY) == 0
    assert days_remaining(date(2026, 8, 23), TODAY) == -1
    assert days_remaining(None) is None


def test_status_boundaries():
    assert deadline_status(date(2026, 9, 12), TODAY) == STATUS_ACTION_REQUIRED  # 19 days
    assert deadline_status(date(2026, 8, 31), TODAY) == STATUS_DUE_SOON  # 7 days
    assert deadline_status(date(2026, 8, 23), TODAY) == STATUS_EXPIRED


def test_status_is_deterministic():
    due = date(2026, 9, 1)
    assert deadline_status(due, TODAY) == deadline_status(due, TODAY)

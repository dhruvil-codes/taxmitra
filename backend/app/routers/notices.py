"""Notice endpoints: citizens, notice cards, notice detail, refusal payload."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.data_store import get_notice, load_citizens, load_notices
from app.rules.deadlines import compute_due_date, days_remaining, deadline_status
from app.rules.notice_types import NoticeCategory, classify_notice, is_supported
from app.rules.refusal import build_refusal

router = APIRouter(prefix="/api", tags=["notices"])


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _due_date_for_notice(notice: dict, category: NoticeCategory) -> date | None:
    if notice.get("response_due_date"):
        return _parse_date(notice["response_due_date"])
    return compute_due_date(_parse_date(notice["issue_date"]), category)


def _title_for_category(category: NoticeCategory) -> dict[str, str]:
    if category == NoticeCategory.INCOME_MISMATCH_143_1A:
        return {
            "en": "Income mismatch - adjustment proposed",
            "hi": "आय बेमेल - संशोधन का प्रस्ताव",
        }
    if category == NoticeCategory.SCRUTINY_142_1:
        return {
            "en": "Scrutiny notice - information requested",
            "hi": "स्क्रूटनी नोटिस - जानकारी मांगी गई",
        }
    return {
        "en": "Notice type not supported by Tax Mitra",
        "hi": "यह नोटिस प्रकार Tax Mitra द्वारा समर्थित नहीं है",
    }


def notice_card(notice: dict) -> dict:
    category = classify_notice(notice)
    due = _due_date_for_notice(notice, category)
    remaining = days_remaining(due)
    return {
        "id": notice["id"],
        "section": notice["section"],
        "category": category.value,
        "supported": is_supported(category),
        "title": _title_for_category(category),
        "amount_in_question": notice["amount_in_question"],
        "issue_date": notice["issue_date"],
        "assessment_year": notice["assessment_year"],
        "due_date": due.isoformat() if due else None,
        "days_remaining": remaining,
        "status": deadline_status(due),
    }


@router.get("/citizens")
def citizens():
    return load_citizens()


@router.get("/notices")
def notices(citizen_id: str | None = Query(default=None)):
    items = load_notices()
    if citizen_id:
        items = [n for n in items if n["citizen_id"] == citizen_id]
    return [notice_card(n) for n in items]


@router.get("/notices/{notice_id}")
def notice_detail(notice_id: str):
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    card = notice_card(notice)
    card["official_text"] = notice["official_text"]
    card["income_source"] = notice["income_source"]
    card["official_reference"] = notice["official_reference"]
    card["citizen_id"] = notice["citizen_id"]
    return card


@router.get("/notices/{notice_id}/refusal")
def notice_refusal(notice_id: str):
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    category = classify_notice(notice)
    if is_supported(category):
        raise HTTPException(status_code=400, detail="This notice is supported; no refusal applies")
    return build_refusal(category)

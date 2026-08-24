"""Guided question trees per notice category.

Tax Mitra asks simple questions instead of handing the citizen a blank box.
The question set is fixed per category and deterministic — it never depends
on a model. Question text is bilingual (RC: en + hi) and supports simple
placeholders ({amount}, {assessment_year}) rendered from notice metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Text = dict[str, str]  # {"en": ..., "hi": ...}

YES_NO_UNSURE_IDS = ("yes", "no", "unsure")


@dataclass(frozen=True)
class Option:
    id: str
    label: Text


@dataclass(frozen=True)
class Question:
    id: str
    text: Text
    help: Text = field(default_factory=dict)
    options: tuple[Option, ...] = (
        Option("yes", {"en": "Yes", "hi": "हाँ"}),
        Option("no", {"en": "No", "hi": "नहीं"}),
        Option("unsure", {"en": "I'm not sure", "hi": "मुझे पक्का नहीं है"}),
    )


_Q_INCOME_MISMATCH: tuple[Question, ...] = (
    Question(
        id="q1_received",
        text={
            "en": "Did you receive this {amount}?",
            "hi": "क्या आपको यह {amount} प्राप्त हुआ था?",
        },
        help={
            "en": "Check the income source mentioned in the notice against your bank records.",
            "hi": "नोटिस में बताई गई आय स्रोत को अपने बैंक रिकॉर्ड से मिलाइए।",
        },
    ),
    Question(
        id="q2_in_return",
        text={
            "en": "Was this income already included in your tax return?",
            "hi": "क्या यह आय आपके टैक्स रिटर्न में पहले से शामिल थी?",
        },
        help={
            "en": "Look at your filed return and Form 26AS/AIS for Assessment Year {assessment_year}.",
            "hi": "मूल्यांकन वर्ष {assessment_year} के लिए अपना दाखिल रिटर्न और फॉर्म 26AS/AIS देखिए।",
        },
    ),
    Question(
        id="q3_documents",
        text={
            "en": "Do you have a document that supports your answer?",
            "hi": "क्या आपके पास अपने उत्तर के समर्थन में कोई दस्तावेज़ है?",
        },
        help={
            "en": "For example: a bank statement, interest certificate, or your return's computation.",
            "hi": "जैसे: बैंक विवरण, ब्याज प्रमाणपत्र, या आपके रिटर्न की गणना।",
        },
    ),
)

QUESTIONS: dict[str, tuple[Question, ...]] = {
    "income_mismatch_143_1a": _Q_INCOME_MISMATCH,
}

_PLACEHOLDER_RENDERERS = {
    "amount": lambda notice: _format_amount(notice.get("amount_in_question")),
    "assessment_year": lambda notice: str(notice.get("assessment_year", "")),
    "income_source": lambda notice: str(notice.get("income_source", "")),
}


def _format_amount(value: Any) -> str:
    try:
        return f"₹{int(value):,}"
    except (TypeError, ValueError):
        return "₹0"


def render_text(text: str, notice: dict) -> str:
    """Replace {amount}-style placeholders in question/help text."""
    for key, renderer in _PLACEHOLDER_RENDERERS.items():
        text = text.replace("{" + key + "}", renderer(notice))
    return text


def get_questions(category_value: str) -> tuple[Question, ...]:
    return QUESTIONS.get(category_value, ())


def valid_answer(value: Any) -> bool:
    return value in YES_NO_UNSURE_IDS

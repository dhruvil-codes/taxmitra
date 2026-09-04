"""Refusal behaviour — honesty as a product feature.

If a notice falls outside the supported workflows, Tax Mitra does not
manufacture confidence. It says so, explains why, and points to official
channels. This payload is deterministic (rules, not AI).
"""

from __future__ import annotations

from app.rules.notice_types import NoticeCategory

OFFICIAL_EFILING_URL = "https://www.incometax.gov.in/iec/foservices/"
OFFICIAL_HELP_URL = "https://www.incometax.gov.in/iec/helpcenter"

_REFUSAL_TEXT = {
    "headline": {
        "en": "This notice is outside Tax Mitra's supported workflows",
        "hi": "यह नोटिस Tax Mitra के समर्थित कार्यप्रवाहों के दायरे में नहीं है",
    },
    "why": {
        "en": "Tax Mitra does not have a notice-specific workflow for this notice type. It therefore cannot interpret the notice or prepare response guidance without risking an unsupported conclusion.",
        "hi": "इस नोटिस प्रकार के लिए Tax Mitra के पास नोटिस-विशिष्ट कार्यप्रवाह नहीं है। इसलिए बिना पर्याप्त आधार के नोटिस की व्याख्या या उत्तर की मार्गदर्शिका देना उचित नहीं होगा।",
    },
    "suggestion": {
        "en": "Notices of this kind can have serious consequences and strict timelines. Consider consulting a chartered accountant or an authorized tax professional before responding.",
        "hi": "इस प्रकार के नोटिस में गंभीर परिणाम और सख़्त समय-सीमाएँ हो सकती हैं। उत्तर देने से पहले किसी चार्टर्ड एकाउंटेंट या अधिकृत कर-विशेषज्ञ से परामर्श लेने पर विचार करें।",
    },
}


def build_refusal(category: NoticeCategory) -> dict:
    return {
        "supported": False,
        "category": category.value,
        "headline": _REFUSAL_TEXT["headline"],
        "why": _REFUSAL_TEXT["why"],
        "suggestion": _REFUSAL_TEXT["suggestion"],
        "official_links": [
            {"label": {"en": "Official Income Tax e-Filing portal", "hi": "आयकर e-Filing पोर्टल (आधिकारिक)"},
             "url": OFFICIAL_EFILING_URL},
            {"label": {"en": "e-Filing help centre", "hi": "e-Filing सहायता केंद्र"},
             "url": OFFICIAL_HELP_URL},
        ],
    }

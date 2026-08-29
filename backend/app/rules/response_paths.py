"""Response path resolution — the heart of "Rules decide".

Given a notice category and the citizen's answers to the guided questions,
this module deterministically resolves: the citizen's position, guidance,
a personalized checklist, and the draft template. Every combination of
answers resolves to exactly one path. The test suite locks all 27 answer
combinations down.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.rules.decision_trees import Question, localized_income_source, render_text
from app.rules.notice_types import NoticeCategory

Text = dict[str, str]

POSITION_AGREE = "agree"
POSITION_DISAGREE = "disagree"
POSITION_NOT_SURE = "not_sure"

EVIDENCE_AVAILABLE = "available"
EVIDENCE_MISSING = "missing"
EVIDENCE_UNSURE = "unsure"


@dataclass(frozen=True)
class ResponsePath:
    path_id: str
    position: str
    headline: Text
    guidance: Text
    checklist_ids: tuple[str, ...]
    draft_template_id: str


# --- Base paths for income mismatch u/s 143(1)(a), keyed by (q1, q2) ---
# q1 = did you receive this income?  q2 = was it already in your return?
_BASE_PATHS: dict[tuple[str, str], ResponsePath] = {
    ("no", "yes"): ResponsePath(
        path_id="disagree_not_received",
        position=POSITION_DISAGREE,
        headline={
            "en": "You disagree: this income was never received by you",
            "hi": "आप असहमत हैं: यह आय आपको प्राप्त ही नहीं हुई",
        },
        guidance={
            "en": "Your response will state that this income was never credited to your account and is not attributable to you — the payer's report may be inaccurate or may belong to someone else. Attach the bank statement for that period to support this.",
            "hi": "आपका उत्तर बताएगा कि यह आय आपके खाते में आई ही नहीं और आपसे संबंधित नहीं है — संभव है कि भुगतानकर्ता की रिपोर्ट गलत हो या किसी अन्य व्यक्ति से संबंधित हो। इसके समर्थन में उस अवधि का बैंक विवरण संलग्न करें।",
        },
        checklist_ids=("doc_bank_statement", "doc_26as", "doc_payer_confirmation"),
        draft_template_id="disagree_not_received",
    ),
    ("no", "no"): None,  # filled below — same journey as (no, yes)
    ("no", "unsure"): None,
    ("unsure", "yes"): ResponsePath(
        path_id="not_sure_verify_payer",
        position=POSITION_NOT_SURE,
        headline={
            "en": "Not sure yet: confirm with the payer what was reported",
            "hi": "अभी पक्का नहीं: भुगतानकर्ता से पुष्टि कीजिए कि क्या रिपोर्ट किया गया",
        },
        guidance={
            "en": "Ask the bank or payer in writing: what amount was reported, for which account, and to whom. Also check accounts of family members — income credited to a relative is a common cause of mismatch. Until this is resolved, your draft will record that you are verifying the information.",
            "hi": "बैंक या भुगतानकर्ता से लिखित में पूछिए: कितनी राशि रिपोर्ट की गई, किस खाते के लिए, और किस व्यक्ति के लिए। परिवार के सदस्यों के खाते भी जाँचिए — अक्सर बेमेल का कारण यही होता है। जब तक पुष्टि न हो जाए, आपका मसौदा यह दर्ज करेगा कि आप जानकारी सत्यापित कर रहे हैं।",
        },
        checklist_ids=("doc_payer_confirmation", "doc_26as", "doc_bank_statement"),
        draft_template_id="not_sure_verify_payer",
    ),
    ("unsure", "no"): None,  # alias — same as (unsure, yes)
    ("unsure", "unsure"): None,
    ("yes", "yes"): ResponsePath(
        path_id="disagree_already_reported",
        position=POSITION_DISAGREE,
        headline={
            "en": "You disagree: this income is already in your return",
            "hi": "आप असहमत हैं: यह आय आपके रिटर्न में पहले से शामिल है",
        },
        guidance={
            "en": "Your response will point out that this income was already included in your return, so the difference is an information-matching issue, not an omission. Attach the relevant pages of your return and a computation of total income so the Department can verify it easily.",
            "hi": "आपका उत्तर बताएगा कि यह आय आपके रिटर्न में पहले से दर्ज है, अतः यह बेमेल सूचना-मिलान की समस्या है, चूक नहीं। आसान सत्यापन के लिए अपने रिटर्न के संबंधित पृष्ठ और कुल आय की गणना संलग्न करें।",
        },
        checklist_ids=("doc_itr_extract", "doc_computation", "doc_26as"),
        draft_template_id="disagree_already_reported",
    ),
    ("yes", "no"): ResponsePath(
        path_id="agree_report_now",
        position=POSITION_AGREE,
        headline={
            "en": "You agree: this income was left out of your return",
            "hi": "आप सहमत हैं: यह आय आपके रिटर्न में छूट गई थी",
        },
        guidance={
            "en": "Your response will accept that this income should be part of your total income. Additional tax and applicable interest may result — the Department will recompute and inform you. This is a routine outcome and accepting a genuine omission avoids penalties later.",
            "hi": "आपका उत्तर स्वीकार करेगा कि यह आय आपकी कुल आय का हिस्सा होनी चाहिए। इससे अतिरिक्त कर और लागू ब्याज हो सकता है — विभाग पुनः गणना कर सूचित करेगा। यह सामान्य परिणाम है, और सही चूक स्वीकारना आगे जुर्माने से बचाता है।",
        },
        checklist_ids=("doc_interest_certificate", "doc_computation", "doc_bank_statement", "doc_26as"),
        draft_template_id="agree_report_now",
    ),
    ("yes", "unsure"): ResponsePath(
        path_id="not_sure_check_return",
        position=POSITION_NOT_SURE,
        headline={
            "en": "Not sure yet: compare your return with your AIS first",
            "hi": "अभी पक्का नहीं: पहले अपने रिटर्न की AIS से तुलना कीजिए",
        },
        guidance={
            "en": "Most mismatches are resolved at this step. Compare the mismatch amount line-by-line with your return and your AIS/26AS statement. If the figure appears in both, your response will disagree; if it is genuinely missing, your response will accept the income.",
            "hi": "अधिकांश बेमेल इसी चरण में सुलझ जाते हैं। बेमेल की राशि को अपने रिटर्न और AIS/26AS विवरण से पंक्ति-दर-पंक्ति मिलाइए। यदि राशि दोनों में है तो उत्तर असहमति होगा; यदि वास्तव में छूटी है तो उत्तर स्वीकृति होगी।",
        },
        checklist_ids=("doc_26as", "doc_itr_extract"),
        draft_template_id="not_sure_check_return",
    ),
}

# q1 dominates: if the income was never received or the citizen is unsure
# whether it was received, q2 cannot change the journey.
_BASE_PATHS[("no", "no")] = _BASE_PATHS[("no", "yes")]
_BASE_PATHS[("no", "unsure")] = _BASE_PATHS[("no", "yes")]
_BASE_PATHS[("unsure", "no")] = _BASE_PATHS[("unsure", "yes")]
_BASE_PATHS[("unsure", "unsure")] = _BASE_PATHS[("unsure", "yes")]


def evidence_from_answers(answers: dict) -> str:
    q3 = answers.get("q3_documents")
    if q3 == "yes":
        return EVIDENCE_AVAILABLE
    if q3 == "no":
        return EVIDENCE_MISSING
    return EVIDENCE_UNSURE


def resolve_path(category: NoticeCategory, answers: dict) -> ResponsePath | None:
    """Total, deterministic resolution. Returns None for unsupported categories."""
    if category != NoticeCategory.INCOME_MISMATCH_143_1A:
        return None
    q1 = answers.get("q1_received")
    q2 = answers.get("q2_in_return")
    path = _BASE_PATHS.get((q1, q2))
    if path is None:
        return None

    evidence = evidence_from_answers(answers)
    if evidence in (EVIDENCE_MISSING, EVIDENCE_UNSURE):
        # No supporting document yet — the first item becomes obtaining one.
        ids = list(path.checklist_ids)
        if "doc_ais_download" not in ids:
            ids.insert(0, "doc_ais_download")
        path = ResponsePath(
            path_id=path.path_id,
            position=path.position,
            headline=path.headline,
            guidance=path.guidance,
            checklist_ids=tuple(ids),
            draft_template_id=path.draft_template_id,
        )
    return path


# ---------------------------------------------------------------------------
# Draft building: the rules engine produces the full structured draft.
# The AI layer may later *polish wording* on a cache miss, but the content,
# positions, and slots are decided here, deterministically.
# ---------------------------------------------------------------------------

_DOCUMENT_SENTENCES: dict[str, str] = {
    EVIDENCE_AVAILABLE: "The supporting documents referred to above are enclosed with this response.",
    EVIDENCE_MISSING: "The supporting documents are being obtained and will be uploaded as soon as they are available.",
    EVIDENCE_UNSURE: "I am in the process of identifying and obtaining the relevant supporting documents.",
}


def build_draft(
    template: str,
    notice: dict,
    citizen: dict,
    answers: dict,
    due_date: date | None,
) -> str:
    today = date.today()
    slots = {
        "citizen_name": citizen.get("name", "Taxpayer"),
        "pan_masked": citizen.get("pan_masked", ""),
        "section": notice.get("section", "143(1)(a)"),
        "din": notice.get("official_reference", ""),
        "assessment_year": str(notice.get("assessment_year", "")),
        "amount": f"₹{notice.get('amount_in_question', 0):,}",
        "income_source": localized_income_source(notice, "en"),  # drafts are English official letters
        "issue_date": notice.get("issue_date", ""),
        "deadline_date": due_date.strftime('%d/%m/%Y') if due_date else "",
        "documents_sentence": _DOCUMENT_SENTENCES[evidence_from_answers(answers)],
        "today_date": today.strftime('%d/%m/%Y'),
    }
    text = template
    for key, value in slots.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def questions_payload(questions: tuple[Question, ...], notice: dict, locale: str) -> list[dict]:
    """Questions serialized for the API, rendered for a specific notice."""
    payload = []
    for q in questions:
        payload.append(
            {
                "id": q.id,
                "text": render_text(q.text.get(locale, q.text["en"]), notice, locale),
                "help": render_text(q.help.get(locale, q.help.get("en", "")), notice, locale),
                "options": [
                    {"id": o.id, "label": o.label.get(locale, o.label["en"])}
                    for o in q.options
                ],
            }
        )
    return payload

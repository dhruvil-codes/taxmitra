"""Universal helper for extracting notice requests, building 1:1 taxpayer questions,
and incorporating taxpayer answers into response generation across all notice types.
"""
from __future__ import annotations

from typing import Any


def get_notice_extracted_requests(notice: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract confirmed/extracted requests from notice data.

    Source of truth is the actual requests in the notice (e.g. synthetic_extraction,
    notice['requests'], or 142(1) scrutiny requests). Never invents requests.
    """
    raw_requests = (notice.get("synthetic_extraction") or {}).get("requests")
    if not raw_requests:
        raw_requests = notice.get("requests")
    if not raw_requests and str(notice.get("section") or "").strip().startswith("142(1)"):
        try:
            from app.rules.scrutiny import build_scrutiny_requests
            built = build_scrutiny_requests(notice)
            raw_requests = [r.__dict__ for r in built]
        except Exception:
            raw_requests = []

    if not isinstance(raw_requests, (list, tuple)):
        return []

    normalized: list[dict[str, Any]] = []
    for idx, req in enumerate(raw_requests):
        if not isinstance(req, dict):
            continue
        req_id = str(req.get("id") or req.get("request_id") or f"req-{idx + 1}")
        orig_text = str(
            req.get("original_text")
            or req.get("source_text")
            or req.get("text")
            or req.get("what_department_is_asking")
            or ""
        ).strip()
        if not orig_text:
            continue

        resp_sec = str(
            req.get("response_section")
            or req.get("technical_term")
            or req.get("title")
            or orig_text[:80]
        ).strip()

        plain = req.get("plain_language_explanation") or req.get("plain_meaning") or req.get("explanation")
        if isinstance(plain, str):
            plain = {"en": plain, "hi": plain}
        elif not isinstance(plain, dict):
            plain = {
                "en": f"The Department requests verifiable records regarding {resp_sec}.",
                "hi": f"विभाग {resp_sec} के संबंध में सत्यापन योग्य रिकॉर्ड का अनुरोध करता है।",
            }

        why = req.get("why_required") or req.get("why_requested")
        if isinstance(why, str):
            why = {"en": why, "hi": why}
        elif not isinstance(why, dict):
            why = {
                "en": "Required to substantiate facts and figures relevant to the tax proceeding.",
                "hi": "कर कार्यवाही से संबंधित तथ्यों और आंकड़ों की पुष्टि के लिए आवश्यक।",
            }

        evidence = req.get("required_evidence") or req.get("possible_evidence") or req.get("evidence") or []
        if isinstance(evidence, (str, dict)):
            evidence = [evidence]

        normalized.append({
            "id": req_id,
            "request_id": req_id,
            "original_text": orig_text,
            "response_section": resp_sec,
            "title": resp_sec,
            "category": req.get("category") or "notice_requisition",
            "plain_language_explanation": plain,
            "why_required": why,
            "required_evidence": list(evidence),
            "citations": list(req.get("citations") or req.get("source_ids") or []),
            "page_number": req.get("page_number") or req.get("page"),
            "source_location": req.get("source_location") or (f"Page {req.get('page_number')}" if req.get("page_number") else None),
        })

    return normalized


def build_answer_the_notice_questions(
    requests: list[dict[str, Any]], locale: str = "en"
) -> list[dict[str, Any]]:
    """Build exactly 1 taxpayer question per extracted request.

    RULE: If notice contains N requests, return N questions.
    Each question clearly explains what the department is asking,
    asks the taxpayer for specific information, provides appropriate options,
    and allows supporting details.
    """
    questions: list[dict[str, Any]] = []

    pos_options = [
        {
            "id": "provide",
            "label": {
                "en": "I have this record and can provide full details",
                "hi": "मेरे पास यह रिकॉर्ड है और मैं पूरा विवरण प्रदान कर सकता हूँ",
            },
        },
        {
            "id": "partial",
            "label": {
                "en": "I have partial information / Need time to obtain records",
                "hi": "मेरे पास आंशिक जानकारी है / रिकॉर्ड प्राप्त करने के लिए समय चाहिए",
            },
        },
        {
            "id": "not_applicable",
            "label": {
                "en": "Does not apply to my return / Disagree with this request",
                "hi": "मेरे रिटर्न पर लागू नहीं / इस अनुरोध से असहमत",
            },
        },
        {
            "id": "explain",
            "label": {
                "en": "Provide specific factual explanation / clarification",
                "hi": "विशिष्ट तथ्यात्मक स्पष्टीकरण या टिप्पणी प्रदान करें",
            },
        },
    ]

    for index, req in enumerate(requests):
        req_id = req["id"]
        qid = f"notice_req_{req_id}"
        title = req["response_section"]
        orig_text = req["original_text"]
        plain = req.get("plain_language_explanation") or {}
        plain_text = plain.get(locale) or plain.get("en") or ""
        why = req.get("why_required") or {}
        why_text = why.get(locale) or why.get("en") or ""

        question_text_dict = {
            "en": f"Requisition {index + 1}: How will you respond regarding \"{title}\"?",
            "hi": f"मांग {index + 1}: \"{title}\" के संबंध में आप क्या जवाब देंगे?",
        }

        help_text_dict = {
            "en": f"The Department is requesting: \"{orig_text}\". Select your position and provide any specific facts, figures, or details below.",
            "hi": f"विभाग मांग रहा है: \"{orig_text}\"। अपनी स्थिति चुनें और नीचे कोई भी विशिष्ट तथ्य, आंकड़े या विवरण दें।",
        }

        questions.append({
            "id": qid,
            "question_id": qid,
            "request_id": req_id,
            "section": "answer_the_notice",
            "section_title": {
                "en": "Answer the Notice",
                "hi": "नोटिस का जवाब दें",
            },
            "item_number": index + 1,
            "total_items": len(requests),
            "text": question_text_dict.get(locale, question_text_dict["en"]),
            "help": help_text_dict.get(locale, help_text_dict["en"]),
            "question_type": "choice_with_other",
            "type": "choice_with_other",
            "options": [
                {
                    "id": opt["id"],
                    "label": opt["label"].get(locale, opt["label"]["en"]),
                }
                for opt in pos_options
            ],
            "required": True,
            "department_request": {
                "title": title,
                "original_text": orig_text,
                "plain_meaning": plain_text,
                "why_required": why_text,
                "page": req.get("page_number"),
                "source_location": req.get("source_location"),
            },
            "allow_details": True,
            "details_placeholder": {
                "en": "Enter specific details, amounts, account numbers, or notes for your response letter (optional):",
                "hi": "अपने उत्तर पत्र के लिए विशिष्ट विवरण, राशि, खाता संख्या या टिप्पणी दर्ज करें (वैकल्पिक):",
            },
        })

    return questions


def extract_taxpayer_request_answer(
    req_id: str, answers: dict[str, Any]
) -> tuple[str, str]:
    """Retrieve position and custom details for a request answer."""
    keys_to_try = [
        f"notice_req_{req_id}",
        req_id,
        f"information_status_{req_id}",
    ]
    raw_val = None
    for k in keys_to_try:
        if k in answers:
            raw_val = answers[k]
            break

    if raw_val is None:
        return ("", "")

    position = ""
    details = ""

    if isinstance(raw_val, dict):
        position = str(raw_val.get("choice") or "").strip()
        details = str(raw_val.get("other") or raw_val.get("details") or "").strip()
    elif isinstance(raw_val, str):
        position = raw_val.strip()

    pos_human_map = {
        "provide": "I have the records and can provide full details.",
        "complete": "I can provide complete records.",
        "partial": "I have partial information or need time to obtain records.",
        "not_applicable": "Not applicable to my return / Disagree with this request.",
        "unavailable": "I cannot provide it / records not available.",
        "explain": "Provide specific factual explanation / clarification.",
        "agree": "Agree — will furnish required particulars.",
        "disagree": "Disagree with the requisition.",
        "yes": "I have the records available.",
        "no": "Records not available / not applicable.",
        "unsure": "Under verification from records.",
    }

    readable_pos = pos_human_map.get(position.lower(), position.replace("_", " ").capitalize())
    return (readable_pos, details)


def format_itemized_request_responses(
    requests: list[dict[str, Any]], answers: dict[str, Any], locale: str = "en"
) -> list[dict[str, Any]]:
    """Format structured items for each request with taxpayer's answers."""
    items: list[dict[str, Any]] = []
    for index, req in enumerate(requests, start=1):
        req_id = req["id"]
        pos, details = extract_taxpayer_request_answer(req_id, answers)
        items.append({
            "item_number": index,
            "request_id": req_id,
            "title": req.get("response_section") or req.get("title") or f"Requisition {index}",
            "department_text": req.get("original_text", ""),
            "taxpayer_position": pos,
            "taxpayer_details": details,
            "evidence": req.get("required_evidence", []),
        })
    return items


def append_notice_answers_to_draft(
    draft: str,
    requests: list[dict[str, Any]],
    answers: dict[str, Any],
    locale: str = "en",
) -> str:
    """Append a taxpayer's 'Answer the Notice' responses to any draft string.

    This is the universal injection point called by the resolve wrapper in
    handlers.py for every notice type.  It appends a clearly-delimited section
    only when there are extracted requests AND the taxpayer provided at least
    one notice-question answer (notice_req_* key present in answers).

    RULE: one request → one answer block in the draft. Never invents content.
    """
    if not requests:
        return draft

    # Only append if user answered at least one notice-request question
    answered_ids = {
        req["id"]
        for req in requests
        if extract_taxpayer_request_answer(req["id"], answers)[0]
    }
    if not answered_ids:
        return draft

    sep = "\n\n" + ("─" * 60) + "\n"
    if locale == "hi":
        header = "नोटिस के प्रश्नों के उत्तर (करदाता द्वारा प्रदत्त):"
        not_answered = "उत्तर नहीं दिया गया"
    else:
        header = "Notice Request Responses (as provided by taxpayer):"
        not_answered = "Not answered"

    lines: list[str] = [sep + header, ""]

    for index, req in enumerate(requests, start=1):
        req_id = req["id"]
        title = req.get("response_section") or req.get("title") or req.get("technical_term") or f"Requisition {index}"
        dept_text = req.get("original_text", "")
        pos, details = extract_taxpayer_request_answer(req_id, answers)

        lines.append(f"{index}. {title}")
        if dept_text:
            lines.append(f"   Department request: {dept_text}")
        lines.append(f"   Taxpayer position: {pos if pos else not_answered}")
        if details:
            lines.append(f"   Supporting details: {details}")
        lines.append("")

    lines.append(
        "Tax Mitra has not submitted this response. The taxpayer must review "
        "all information above and submit through the official e-Filing portal."
        if locale != "hi"
        else "Tax Mitra ने यह उत्तर जमा नहीं किया है। करदाता को सभी जानकारी की समीक्षा करनी चाहिए।"
    )

    return draft + "\n".join(lines)

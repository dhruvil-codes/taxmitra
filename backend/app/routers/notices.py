"""Notice endpoints: citizens, notice cards, notice detail, refusal payload."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.data_store import get_notice, load_citizens, load_notices
from app.rules.deadlines import compute_due_date, days_remaining, deadline_status
from app.rules.notice_types import NoticeCategory, classify_notice, is_supported
from app.rules.refusal import build_refusal
from app.workflows.registry import WorkflowCapability, classify_extracted_notice, get_workflow, list_workflows
from app.workflows.registry import classify_ai_proposal
from app.workflows.handlers import get_workflow_handler, grounding_payload
from app.workflows.official import official_portal_payload
from app.extraction.pdf import MAX_PDF_BYTES
from app.extraction.pdf import extract_pdf
from app.ingestion.pipeline import ingest_pdf
from app.extraction.sessions import confirm_session, create_session, get_session
from app.ai.notice_classifier import classify_notice_with_ai
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["notices"])


class WorkflowClassificationRequest(BaseModel):
    notice: dict[str, object]
    grounding: dict[str, object] | None = None


class WorkflowExtractionConfirmation(BaseModel):
    extraction_id: str
    fingerprint: str
    confirmed: bool
    corrections: dict[str, str] = {}


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _session_notice(notice_id: str) -> dict | None:
    session = get_session(notice_id)
    if not session or not session.get("confirmed"):
        return None
    metadata = session.get("metadata", {})
    stored = dict(session.get("notice") or {})
    return {
        **stored,
        "id": notice_id,
        "section": metadata.get("section"),
        "assessment_year": metadata.get("assessment_year") or "unknown",
        "response_due_date": metadata.get("response_deadline"),
        "issue_date": metadata.get("issue_date"),
        "official_reference": metadata.get("notice_reference"),
        "amount_in_question": 0,
        "income_source": "Uploaded notice",
        "official_text": "\n".join(page.get("text", "") for page in session.get("pages", [])),
        "citizen_id": "uploaded",
        "synthetic_extraction": {**(stored.get("synthetic_extraction") or {}), "source_type": "pdf", "requires_human_confirmation": True, "requests": session.get("requests", [])},
    }


def _due_date_for_notice(notice: dict, category: NoticeCategory) -> date | None:
    if notice.get("response_due_date"):
        return _parse_date(notice["response_due_date"])
    return compute_due_date(_parse_date(notice["issue_date"]), category) if notice.get("issue_date") else None


def _title_for_category(category: NoticeCategory) -> dict[str, str]:
    if category == NoticeCategory.DEFECTIVE_RETURN_139_9:
        return {
            "en": "139(9) defective return notice",
            "hi": "धारा 139(9) दोषपूर्ण रिटर्न नोटिस",
        }
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
    classification = classify_extracted_notice(notice)
    workflow = get_workflow(category.value)
    due = _due_date_for_notice(notice, category)
    remaining = days_remaining(due)
    return {
        "id": notice["id"],
        "section": notice["section"],
        "category": category.value,
        "supported": is_supported(category),
        "workflow_id": workflow.workflow_id if workflow else "unsupported",
        "workflow_status": classification.status,
        "classification_confidence": classification.confidence,
        "classification_grounding_status": classification.grounding_status,
        "frontend_entry": workflow.frontend_entry if workflow else "unsupported",
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
        notice = _session_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    card = notice_card(notice)
    card["official_text"] = notice["official_text"]
    card["income_source"] = notice["income_source"]
    card["official_reference"] = notice["official_reference"]
    card["citizen_id"] = notice["citizen_id"]
    return card


@router.get("/workflows")
def workflows():
    """Return the generic workflow contract for frontend routing and display."""
    return {"workflows": list_workflows()}


@router.post("/workflows/classify")
def classify_workflow(payload: WorkflowClassificationRequest):
    """Classify extracted content while preserving confidence and safe-stop state."""
    return classify_extracted_notice(payload.notice, payload.grounding).payload()


@router.post("/workflows/extract")
async def extract_workflow(file: UploadFile = File(...)):
    """Universal extraction boundary; workflow handlers remain separate."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only application/pdf is accepted")
    content = await file.read(MAX_PDF_BYTES + 1)
    result = ingest_pdf(content, file.filename, file.content_type)
    text = "\n".join(page.get("text", "") for page in result.pages).strip()
    notice = {
        **result.metadata,
        "section": result.metadata.get("section"),
        "official_text": text,
        "pages": list(result.pages),
        "synthetic_extraction": {"requests": list(result.requests)},
    }
    grounding = {
        "confidence": result.confidence,
        "below_floor": result.confidence < 0.7,
        "verified": False,
    }
    ai_proposal, ai_warning = classify_notice_with_ai(notice, get_settings())
    classification = classify_ai_proposal(notice, ai_proposal, grounding) if ai_proposal else classify_extracted_notice(notice, grounding)
    workflow = get_workflow(classification.category)
    metadata = dict(result.metadata)
    if not metadata.get("section") and ai_proposal and isinstance(ai_proposal.get("section"), str) and ai_proposal["section"].strip():
        metadata["section"] = ai_proposal["section"].strip()
    safe_stop = bool(result.refusal_reason) or classification.status == "safe_stop"
    refusal_reason = result.refusal_reason
    if classification.category == "not_income_tax_document":
        safe_stop = True
        if not refusal_reason:
            refusal_reason = "not_income_tax_document"
    elif classification.status == "safe_stop":
        safe_stop = True

    enriched_requests = []
    for idx, req in enumerate(result.requests):
        orig_text = req.get("original_text", "")
        enriched_requests.append({
            "request_id": req.get("request_id") or f"req-{idx+1}",
            "id": req.get("request_id") or f"req-{idx+1}",
            "original_text": orig_text,
            "page_number": req.get("page_number", 1),
            "response_section": req.get("response_section"),
            "plain_language_explanation": req.get("plain_language_explanation") or {
                "en": "Verification of records specified by the assessing authority.",
                "hi": "कर निर्धारण अधिकारी द्वारा निर्दिष्ट अभिलेखों का सत्यापन।",
            },
            "why_required": req.get("why_required") or {
                "en": "Required to substantiate claims made in the return of income.",
                "hi": "आय के विवरण में किए गए दावों की पुष्टि के लिए आवश्यक।",
            },
            "required_evidence": list(req.get("required_evidence") or ["Relevant supporting documentary proof"]),
            "citations": list(req.get("citations") or ["sec-142-0001"]),
            "confidence": float(req.get("confidence", 1.0)),
            "warnings": list(req.get("warnings") or []),
        })

    payload = {
        "supported": not safe_stop,
        "status": "safe_stop" if safe_stop else "needs_confirmation",
        "metadata": metadata,
        "extraction": {
            "status": result.status,
            "confidence": result.confidence,
            "warnings": list(result.warnings) + ([ai_warning] if ai_warning else []),
            "refusal_reason": refusal_reason,
            "method": result.extraction_method,
            "page_count": result.page_count,
        },
        "classification": classification.payload(),
        "workflow": workflow.payload() if workflow else None,
        "requests": enriched_requests,
        "pages": list(result.pages),
    }
    # Use the same short-lived confirmation boundary as the legacy scrutiny
    # API, while retaining the classified workflow for the generic path.
    if not safe_stop:
        extraction_id, fingerprint = create_session({
            **payload,
            "notice": notice,
            "requests": enriched_requests,
            "workflow_id": classification.workflow_id,
            "original_pdf_sha256": result.original_pdf_sha256,
        }, content)
        payload.update({"extraction_id": extraction_id, "fingerprint": fingerprint, "requires_human_confirmation": True})
    return payload


@router.post("/workflows/confirm")
def confirm_workflow(payload: WorkflowExtractionConfirmation):
    if not payload.confirmed:
        return {"supported": False, "status": "refused", "reason": "Human confirmation was not provided."}
    session = confirm_session(payload.extraction_id, payload.fingerprint, payload.corrections)
    if session is None:
        raise HTTPException(status_code=409, detail="Extraction session or fingerprint is invalid or expired")
    workflow_id = session.get("workflow_id")
    workflow = get_workflow(workflow_id)
    if workflow is None or workflow.capability is WorkflowCapability.SAFE_STOP:
        return {"supported": False, "status": "safe_stop", "frontend_entry": "unsupported"}
    return {
        "supported": True,
        "status": "confirmed",
        "extraction_id": payload.extraction_id,
        "notice_id": payload.extraction_id,
        "workflow_id": workflow.workflow_id,
        "frontend_entry": workflow.frontend_entry,
        "capability": workflow.capability.value,
    }


@router.get("/notices/{notice_id}/workflow")
def notice_workflow(notice_id: str):
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    preliminary = classify_extracted_notice(notice)
    classification = classify_extracted_notice(notice, grounding_payload(notice, preliminary.category))
    workflow = get_workflow(classification.category)
    # Ensure contract has complete data even for SAFE_STOP workflows
    fallback_title = {"en": "Income Tax communication", "hi": "आयकर संचार"}
    contract = {
        "identity": {"workflow_id": classification.workflow_id, "category": classification.category, "title": (workflow.title if workflow else fallback_title)},
        "capability": workflow.capability.value if workflow else "SAFE_STOP",
        "confidence": classification.confidence,
        "grounding_status": classification.grounding_status,
        "reason": classification.reason,
        "notice_facts": {key: notice.get(key) for key in ("section", "assessment_year", "issue_date", "response_due_date", "official_reference")},
        "requests": [],
        "questions": [],
        "evidence": [],
        "safe_stop": {"reason": classification.reason, "facts": {"section": notice.get("section"), "deadline": notice.get("response_due_date")}},
        "official_portal": official_portal_payload(),
        "grounding": grounding_payload(notice, classification.category),
    }
    if workflow:
        handler = get_workflow_handler(classification.category)
        question_payload = handler.get_questions(notice, "en")
        contract["questions"] = question_payload.get("questions", [])
        contract["requests"] = question_payload.get("requests", [])
        contract["evidence"] = handler.get_evidence(notice)
        contract["notice_facts"].update(question_payload.get("facts") or {})
        contract["next_steps"] = [workflow.official_next_step]
    else:
        # Fallback to raw requests for SAFE_STOP workflows
        contract["requests"] = list((notice.get("synthetic_extraction") or {}).get("requests") or [])
        # Ensure SAFE_STOP workflows always have complete contract data
        contract["next_steps"] = ["Review the communication and its deadline.", "Use the official Income Tax e-Filing portal for any required action."]
    payload = {
        "notice_id": notice_id,
        "classification": classification.payload(),
        "workflow": workflow.payload() if workflow else None,
        "contract": contract,
    }
    return payload


@router.get("/notices/{notice_id}/refusal")
def notice_refusal(notice_id: str):
    notice = get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    category = classify_notice(notice)
    if is_supported(category):
        raise HTTPException(status_code=400, detail="This notice is supported; no refusal applies")
    return build_refusal(category)

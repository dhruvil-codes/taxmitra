"""Common workflow handler boundary for supported and safe-stop workflows.

Handlers deliberately delegate to the existing deterministic rule modules. This
gives the API one extension point without duplicating or weakening those rules.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Any


def _grounding_for(notice: dict[str, Any], category: str):
    from app.config import get_settings
    from app.knowledge.grounding import ground

    text = "\n".join(str(notice.get(key) or "") for key in ("section", "official_text", "department_terminology"))
    for request in (notice.get("synthetic_extraction") or {}).get("requests") or []:
        text += "\n" + " ".join(str(request.get(key) or "") for key in ("original_text", "response_section", "category"))
    return ground(
        get_settings(),
        f"{category} {text}",
        assessment_year=notice.get("assessment_year"),
        tax_year=notice.get("tax_year"),
        act_version=notice.get("act_version"),
        workflow_context=category,
    )


def grounding_payload(notice: dict[str, Any], category: str) -> dict[str, Any]:
    result = _grounding_for(notice, category)
    return {
        "method": result.method,
        "confidence": result.confidence,
        "below_floor": result.below_floor,
        "ambiguous": result.ambiguous,
        "reason": result.reason,
        "sources": [{
            "id": chunk.id,
            "title": chunk.title,
            "section": chunk.section,
            "official_url": chunk.official_url,
            "source": chunk.source_name,
            "status": chunk.status,
            "verification_status": chunk.verification_status,
            "assessment_year": chunk.assessment_year,
            "tax_year": chunk.tax_year,
            "act_version": chunk.act_version,
        } for chunk in result.chunks if chunk.official_url.startswith("https://www.incometax.gov.in/")],
    }


class WorkflowHandler(ABC):
    category: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for method_name in ("get_questions", "resolve"):
            original = cls.__dict__.get(method_name)
            if original is None or getattr(original, "_grounded", False):
                continue
            if method_name == "get_questions":
                def get_questions(self, notice, locale="en", answers=None, _original=original, **kw):
                    result = _original(self, notice, locale=locale, answers=answers, **kw)
                    if isinstance(result, dict):
                        result = dict(result)
                        result.setdefault("grounding", grounding_payload(notice, self.category))
                        from app.workflows.notice_requests import get_notice_extracted_requests, build_answer_the_notice_questions
                        extracted = get_notice_extracted_requests(notice)
                        if "requests" not in result or not result["requests"]:
                            result["requests"] = extracted
                        notice_qs = build_answer_the_notice_questions(extracted, locale=locale)
                        sit_qs = [dict(q) if isinstance(q, dict) else q for q in (result.get("situation_questions") or result.get("questions") or [])]
                        for q in sit_qs:
                            if isinstance(q, dict):
                                q.setdefault("section", "understand_situation")
                        result["situation_questions"] = sit_qs
                        result["notice_questions"] = notice_qs
                    return result
                get_questions._grounded = True
                setattr(cls, method_name, get_questions)
            else:
                def resolve(self, notice, answers, _original=original, **kwargs):
                    result = _original(self, notice, answers, **kwargs)
                    if isinstance(result, dict):
                        result = dict(result)
                        result.setdefault("grounding", grounding_payload(notice, self.category))
                        # Universal: append taxpayer "Answer the Notice" responses to any draft.
                        # Runs for every handler — only adds content if notice_req_* answers exist.
                        # Skips if the draft was already produced by format_formal_reply_letter
                        # (which handles notice answers inline, e.g. 142(1) scrutiny).
                        draft = result.get("draft")
                        already_has_answers = (
                            "Notice Request Responses" in draft
                            or "Taxpayer details:" in draft
                            or "Taxpayer position:" in draft
                            or "(As per Annexure \u2014" in draft  # formal letter already embedded answers
                        ) if isinstance(draft, str) else True
                        if isinstance(draft, str) and not already_has_answers:
                            try:
                                from app.workflows.notice_requests import (
                                    get_notice_extracted_requests,
                                    append_notice_answers_to_draft,
                                )
                                locale = kwargs.get("locale", "en")
                                extracted = get_notice_extracted_requests(notice)
                                result["draft"] = append_notice_answers_to_draft(
                                    draft, extracted, answers, locale=locale
                                )
                            except Exception:
                                pass  # Never block resolve due to draft enrichment
                    return result
                resolve._grounded = True
                setattr(cls, method_name, resolve)

    @abstractmethod
    def get_questions(self, notice: dict[str, Any], locale: str = "en", answers: dict[str, Any] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def resolve(self, notice: dict[str, Any], answers: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def get_evidence(self, notice: dict[str, Any], statuses: dict[str, str] | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def generate_response(self, notice: dict[str, Any], answers: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def review(self, notice: dict[str, Any], answers: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...


class Scrutiny142Handler(WorkflowHandler):
    category = "scrutiny_142_1"

    def _requests(self, notice: dict[str, Any], confirmed: bool = True):
        from app.rules.scrutiny import build_scrutiny_requests
        return build_scrutiny_requests(notice, confirmed)

    def get_questions(self, notice, locale="en", answers=None):
        from app.rules.scrutiny import minimum_question_plan, minimum_question_plan_payload
        requests = self._requests(notice)
        plan = minimum_question_plan(requests, answers)
        return {"questions": minimum_question_plan_payload(plan, locale), "requests": [r.__dict__ for r in requests]}

    def resolve(self, notice, answers, **kwargs):
        from app.rules.scrutiny import resolve_minimum_scrutiny
        return resolve_minimum_scrutiny(notice, answers, kwargs.get("document_statuses", {}), kwargs.get("extraction_confirmed", True))

    def get_evidence(self, notice, statuses=None):
        from app.evidence.mapping import map_evidence
        return map_evidence(self._requests(notice), statuses)

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)


class IncomeMismatch143Handler(WorkflowHandler):
    category = "income_mismatch_143_1a"

    def get_questions(self, notice, locale="en", answers=None):
        from app.rules.decision_trees import get_questions
        from app.rules.response_paths import questions_payload
        return {"questions": questions_payload(get_questions(self.category), notice, locale)}

    def resolve(self, notice, answers, **kwargs):
        from app.rules.decision_trees import get_questions, valid_answer
        from app.rules.response_paths import resolve_path, build_draft
        from app.rules.checklists import checklist_for
        from app.rules.deadlines import compute_due_date, days_remaining, deadline_status
        from app.data_store import get_citizen, load_draft_templates
        from datetime import date
        expected = {question.id for question in get_questions(self.category)}
        if not expected.issubset(answers):
            raise ValueError(f"Missing answers for: {sorted(expected - set(answers))}")
        if any(key in expected and not valid_answer(value) for key, value in answers.items()):
            raise ValueError("Invalid answer")
        path = resolve_path(self.category, answers)
        if path is None:
            return {"supported": False, "status": "safe_stop"}

        raw_issue_date = notice.get("issue_date")
        parsed_issue_date = None
        if isinstance(raw_issue_date, date):
            parsed_issue_date = raw_issue_date
        elif isinstance(raw_issue_date, str) and raw_issue_date.strip():
            try:
                parsed_issue_date = date.fromisoformat(raw_issue_date.strip())
            except (ValueError, TypeError):
                parsed_issue_date = None

        due = compute_due_date(parsed_issue_date, self.category) if parsed_issue_date else None
        if due is None and notice.get("response_due_date"):
            raw_response_due = notice.get("response_due_date")
            if isinstance(raw_response_due, date):
                due = raw_response_due
            elif isinstance(raw_response_due, str) and raw_response_due.strip():
                try:
                    due = date.fromisoformat(raw_response_due.strip())
                except (ValueError, TypeError):
                    due = None

        template = load_draft_templates()[path.draft_template_id]
        safe_notice = dict(notice)
        if safe_notice.get("issue_date") is None:
            safe_notice["issue_date"] = ""
        citizen = get_citizen(notice.get("citizen_id")) or {}
        draft = build_draft(template, safe_notice, citizen, answers, due)

        # If the notice has extracted requests, produce the authentic formal letter instead
        from app.workflows.notice_requests import get_notice_extracted_requests
        extracted = get_notice_extracted_requests(notice)
        if extracted:
            from app.rules.letter_templates import format_formal_reply_letter
            draft = format_formal_reply_letter(
                notice=notice,
                requests=extracted,
                answers=answers,
                due_date=due.isoformat() if due else None,
            )

        return {"supported": True, "path": {"path_id": path.path_id, "position": path.position, "headline": path.headline, "guidance": path.guidance}, "checklist": [{"id": item.id, "title": item.title, "why_needed": item.why_needed} for item in checklist_for(path.checklist_ids)], "deadline": {"due_date": due.isoformat() if due else None, "days_remaining": days_remaining(due), "status": deadline_status(due)}, "draft": draft, "portal_navigation_path": {"en": "e-Proceedings", "hi": "e-Proceedings"}}

    def get_evidence(self, notice, statuses=None):
        from app.rules.checklists import checklist_for
        return [{"id": item.id, "title": item.title, "why_needed": item.why_needed} for item in checklist_for(())]

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        approved = bool(kwargs.get("approved", False))
        return {"status": "approved" if approved else "blocked", "handoff_allowed": approved, "message": "Official handoff remains blocked until explicit human approval." if not approved else "Response is ready for the taxpayer's official portal review."}


class Rectification154Handler(WorkflowHandler):
    """Guided section 154 routing; never treats disagreement as a mistake."""

    category = "rectification_154"
    official_source = "https://www.incometax.gov.in/iec/foportal/help/how-to-perform-rectification?mobile-app=1"

    def _facts(self, notice):
        facts = notice.get("rectification_facts") or (notice.get("synthetic_extraction") or {}).get("rectification_facts") or {}
        issue = str(facts.get("issue_type") or "").lower()
        aliases = {"reprocess": "reprocess_return", "tax_credit": "tax_credit_mismatch", "return_data": "return_data_correction"}
        issue = aliases.get(issue, issue)
        if issue not in {"reprocess_return", "tax_credit_mismatch", "return_data_correction"}:
            issue = "unknown"
        return {**facts, "issue_type": issue, "disagreement_only": bool(facts.get("disagreement_only", False)), "mistake_apparent": facts.get("mistake_apparent")}

    def get_questions(self, notice, locale="en", answers=None):
        facts = self._facts(notice)
        questions = [{
            "id": "rectification_record_confirmed", 
            "question_type": "single_choice", 
            "text": {
                "en": "Do the issue and records shown here match the communication?",
                "hi": "क्या यहां दिखाई गई समस्या और रिकॉर्ड संचार से मेल खाते हैं?"
            },
            "help": {
                "en": "Rectification must be based on a mistake apparent from the record, not only disagreement with the result.",
                "hi": "सुधार केवल रिकॉर्ड से स्पष्ट गलती के आधार पर होना चाहिए, न कि केवल परिणाम से असहमति के आधार पर।"
            },
            "options": [
                {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}}, 
                {"id": "no", "label": {"en": "No", "hi": "नहीं"}}, 
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
            ], 
            "required": True
        }]
        if facts["issue_type"] == "unknown":
            questions.append({
                "id": "rectification_issue_type", 
                "question_type": "single_choice", 
                "text": {
                    "en": "Which issue is clearly shown in the record?",
                    "hi": "रिकॉर्ड में कौन सी समस्या स्पष्ट रूप से दिखाई दे रही है?"
                },
                "help": {
                    "en": "This selects the official request type; do not choose one if the record does not support it.",
                    "hi": "यह आधिकारिक अनुरोध प्रकार चुनता है; यदि रिकॉर्ड इसका समर्थन नहीं करता तो इसे न चुनें।"
                },
                "options": [
                    {"id": "reprocess_return", "label": {"en": "CPC did not consider correct return data", "hi": "CPC ने सही रिटर्न डेटा नहीं माना"}}, 
                    {"id": "tax_credit_mismatch", "label": {"en": "TDS, TCS or tax credit details", "hi": "TDS, TCS या कर क्रेडिट विवरण"}}, 
                    {"id": "return_data_correction", "label": {"en": "Incorrect return data needs correction", "hi": "गलत रिटर्न डेटा को सुधार की आवश्यकता है"}}, 
                    {"id": "not_sure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
                ], 
                "conditions": [{"depends_on": "rectification_record_confirmed", "equals": "yes"}], 
                "required": True
            })
        if facts.get("mistake_apparent") is None:
            questions.append({
                "id": "mistake_apparent", 
                "question_type": "single_choice", 
                "text": {
                    "en": "Is there a specific mistake apparent from the existing record?",
                    "hi": "क्या मौजूदा रिकॉर्ड से कोई विशिष्ट गलती स्पष्ट है?"
                },
                "help": {
                    "en": "A rectification request is not appropriate merely because you disagree with the outcome or want to add a new claim.",
                    "hi": "केवल इसलिए कि आप परिणाम से असहमत हैं या नया दावा जोड़ना चाहते हैं, सुधार अनुरोध उचित नहीं है।"
                },
                "options": [
                    {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}}, 
                    {"id": "no", "label": {"en": "No", "hi": "नहीं"}}, 
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
                ], 
                "conditions": [{"depends_on": "rectification_record_confirmed", "equals": "yes"}], 
                "required": True
            })
        
        # Localize the questions based on locale
        localized_questions = []
        for q in questions:
            localized_q = {
                "id": q["id"],
                "question_type": q["question_type"],
                "text": q["text"].get(locale, q["text"]["en"]),
                "help": q["help"].get(locale, q["help"]["en"]),
                "options": [{"id": opt["id"], "label": opt["label"].get(locale, opt["label"]["en"])} for opt in q["options"]],
                "required": q.get("required", False)
            }
            if "conditions" in q:
                localized_q["conditions"] = q["conditions"]
            localized_questions.append(localized_q)
        
        return {"questions": localized_questions, "facts": facts}

    def get_evidence(self, notice, statuses=None):
        statuses = statuses or {}
        facts = self._facts(notice)
        items = [{"request_id": "154", "document_id": "154-intimation", "document_name": {"en": "Original CPC intimation/order", "hi": "मूल CPC सूचना/आदेश"}, "reason": {"en": "Use the exact processed figures and communication reference.", "hi": "प्रसंस्कृत आंकड़ों और संचार संदर्भ के लिए मूल सूचना रखें।"}, "requirement_level": "required", "status": statuses.get("154-intimation", "not_sure"), "source": [self.official_source]}]
        if facts["issue_type"] in {"reprocess_return", "return_data_correction"}:
            items.append({"request_id": "154", "document_id": "154-filed-return", "document_name": {"en": "Filed return and original schedules", "hi": "दाखिल रिटर्न और मूल अनुसूचियां"}, "reason": {"en": "Compare the data already filed with the CPC processing record.", "hi": "पहले दाखिल डेटा की CPC रिकॉर्ड से तुलना करें।"}, "requirement_level": "required", "status": statuses.get("154-filed-return", "not_sure"), "source": [self.official_source]})
        if facts["issue_type"] == "tax_credit_mismatch":
            items.append({"request_id": "154", "document_id": "154-tax-credit-records", "document_name": {"en": "Form 26AS and TDS/TCS/challan records", "hi": "फॉर्म 26AS और TDS/TCS/चालान रिकॉर्ड"}, "reason": {"en": "Compare only the credit details already reflected in the Department record.", "hi": "केवल विभागीय रिकॉर्ड में दिख रहे क्रेडिट विवरण की तुलना करें।"}, "requirement_level": "required", "status": statuses.get("154-tax-credit-records", "not_sure"), "source": [self.official_source]})
        return items

    def resolve(self, notice, answers, **kwargs):
        facts = self._facts(notice)
        if answers.get("rectification_record_confirmed") != "yes":
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The rectification facts were not confirmed against the record."}
        if facts.get("disagreement_only") or answers.get("mistake_apparent") in {"no", "unsure"} or facts.get("mistake_apparent") is False:
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "Rectification is not appropriate merely because the taxpayer disagrees; a mistake apparent from the record must be confirmed."}
        issue = facts["issue_type"] if facts["issue_type"] != "unknown" else answers.get("rectification_issue_type")
        if issue not in {"reprocess_return", "tax_credit_mismatch", "return_data_correction"} or answers.get("mistake_apparent") != "yes" and facts.get("mistake_apparent") is not True:
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The rectification type or record-based mistake was not confirmed."}
        guidance = {"reprocess_return": "Use Reprocess the Return when true and correct return particulars were already furnished but CPC did not consider them.", "tax_credit_mismatch": "Use Tax Credit Mismatch Correction for TDS, TCS or tax/challan details shown in the return and Form 26AS.", "return_data_correction": "Use Return Data Correction only to correct existing return data; do not add a new income source or additional deduction."}[issue]
        return {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "path": {"path_id": issue, "headline": guidance, "official_source": self.official_source}, "action": guidance, "draft": f"Rectification action plan (review before use):\n{guidance}\n\nTax Mitra has not submitted a rectification request.", "checklist": self.get_evidence(notice), "handoff_allowed": False, "next_step": "Review the request type, existing records and all entries on the official e-Filing portal before submitting.", "facts": facts, "portal_navigation_path": {"en": "Services → Rectification", "hi": "Services → Rectification"}}

    def generate_response(self, notice, answers, **kwargs): return self.resolve(notice, answers, **kwargs)
    def review(self, notice, answers, **kwargs): return {"status": "approved" if kwargs.get("approved") else "blocked", "handoff_allowed": False, "message": "Review is required before using the official Rectification service."}


class TaxCreditMismatchHandler(Rectification154Handler):
    """Tax-credit route with explicit taxpayer-versus-deductor branching."""
    category = "tax_credit_tds_mismatch"
    official_source = "https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/tax-credit-mismatch/tax-UM"

    def _facts(self, notice):
        facts = super()._facts(notice)
        raw = notice.get("tax_credit_facts") or (notice.get("synthetic_extraction") or {}).get("tax_credit_facts") or {}
        credit_type = str(raw.get("credit_type") or facts.get("credit_type") or "").lower()
        if credit_type not in {"tds", "tcs", "advance_tax", "self_assessment_tax", "other_tax_credit"}:
            credit_type = "unknown"
        return {**facts, **raw, "issue_type": "tax_credit_mismatch", "credit_type": credit_type, "taxpayer_side_error": raw.get("taxpayer_side_error"), "deductor_side_error": raw.get("deductor_side_error")}

    def get_questions(self, notice, locale="en", answers=None):
        facts = self._facts(notice)
        questions = [{
            "id": "credit_record_confirmed", 
            "question_type": "single_choice", 
            "text": {
                "en": "Do the mismatch details match your return and Form 26AS?",
                "hi": "क्या बेमेल विवरण आपके रिटर्न और फॉर्म 26AS से मेल खाते हैं?"
            },
            "help": {
                "en": "Tax Mitra will not invent or change a credit value.",
                "hi": "Tax Mitra कोई क्रेडिट मान नहीं बनाएगा या नहीं बदलेगा।"
            },
            "options": [
                {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}}, 
                {"id": "no", "label": {"en": "No", "hi": "नहीं"}}, 
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
            ], 
            "required": True
        }]
        if facts["credit_type"] == "unknown":
            questions.append({
                "id": "credit_type", 
                "question_type": "single_choice", 
                "text": {
                    "en": "Which type of credit is shown as mismatched?",
                    "hi": "किस प्रकार का क्रेडिट बेमेल दिखाया गया है?"
                },
                "help": {
                    "en": "This determines whether the portal checklist concerns TDS, TCS or a tax challan.",
                    "hi": "यह तय करता है कि पोर्टल चेकलिस्ट TDS, TCS या कर चालान से संबंधित है।"
                },
                "options": [
                    {"id": "tds", "label": {"en": "TDS", "hi": "TDS"}}, 
                    {"id": "tcs", "label": {"en": "TCS", "hi": "TCS"}}, 
                    {"id": "advance_tax", "label": {"en": "Advance tax", "hi": "अग्रिम कर"}}, 
                    {"id": "self_assessment_tax", "label": {"en": "Self-assessment tax", "hi": "स्व-मूल्यांकन कर"}}, 
                    {"id": "other_tax_credit", "label": {"en": "Other tax credit", "hi": "अन्य कर क्रेडिट"}}, 
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
                ], 
                "conditions": [{"depends_on": "credit_record_confirmed", "equals": "yes"}], 
                "required": True
            })
        questions.append({
            "id": "correction_owner", 
            "question_type": "single_choice", 
            "text": {
                "en": "Where does the correction appear to be needed?",
                "hi": "सुधार कहाँ आवश्यक प्रतीत होता है?"
            },
            "help": {
                "en": "For TDS/TCS reporting errors, the deductor/collector may need to file a correction statement. Incorrect taxpayer-entered challan or return data may need taxpayer-side correction.",
                "hi": "TDS/TCS रिपोर्टिंग त्रुटियों के लिए, कर्ता/संग्रहकर्ता को सुधार विवरण दाखिल करने की आवश्यकता हो सकती है। गलत करदाता-दर्ज चालान या रिटर्न डेटा को करदाता-पक्ष सुधार की आवश्यकता हो सकती है।"
            },
            "options": [
                {"id": "taxpayer", "label": {"en": "My return or challan details", "hi": "मेरे रिटर्न या चालान विवरण"}}, 
                {"id": "deductor", "label": {"en": "Employer, deductor or collector reporting", "hi": "नियोक्ता, कर्ता या संग्रहकर्ता रिपोर्टिंग"}}, 
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
            ], 
            "conditions": [{"depends_on": "credit_record_confirmed", "equals": "yes"}], 
            "required": True
        })
        
        # Localize the questions based on locale
        localized_questions = []
        for q in questions:
            localized_q = {
                "id": q["id"],
                "question_type": q["question_type"],
                "text": q["text"].get(locale, q["text"]["en"]),
                "help": q["help"].get(locale, q["help"]["en"]),
                "options": [{"id": opt["id"], "label": opt["label"].get(locale, opt["label"]["en"])} for opt in q["options"]],
                "required": q.get("required", False)
            }
            if "conditions" in q:
                localized_q["conditions"] = q["conditions"]
            localized_questions.append(localized_q)
        
        return {"questions": localized_questions, "facts": facts}

    def resolve(self, notice, answers, **kwargs):
        facts = self._facts(notice)
        if answers.get("credit_record_confirmed") != "yes":
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The tax-credit mismatch was not confirmed against the return and Form 26AS."}
        credit_type = facts["credit_type"] if facts["credit_type"] != "unknown" else answers.get("credit_type")
        owner = answers.get("correction_owner")
        if credit_type not in {"tds", "tcs", "advance_tax", "self_assessment_tax", "other_tax_credit"} or owner in {None, "unsure"}:
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The credit type or correction owner is uncertain; Tax Mitra will not choose a taxpayer or deductor correction path."}
        if owner == "deductor":
            action = "Ask the employer, deductor or collector to verify the statement and file the appropriate correction. Tax Mitra has not changed any tax credit."
            path = "deductor_correction"
        else:
            action = "Review the Tax Credit Mismatch Correction or applicable rectification route using only credit and challan details reflected in Form 26AS."
            path = "taxpayer_correction"
        return {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "path": {"path_id": path, "credit_type": credit_type, "headline": action, "official_source": self.official_source}, "action": action, "draft": f"Tax-credit action plan (review before use):\n{action}\n\nNo tax-credit value was created or changed by Tax Mitra.", "checklist": self.get_evidence(notice), "handoff_allowed": False, "next_step": "Review the official Tax Credit Mismatch service and submit only after verifying the displayed records.", "facts": facts, "portal_navigation_path": {"en": "Services → Rectification", "hi": "Services → Rectification"}}


class Demand245Handler(WorkflowHandler):
    """Guided response preparation for outstanding demand and section 245."""

    category = "demand_adjustment_245"
    official_source = "https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/response-outstanding-demand-UM?mobile-app=1"

    def _facts(self, notice):
        facts = notice.get("demand_facts") or (notice.get("synthetic_extraction") or {}).get("demand_facts") or {}
        amount = facts.get("demand_amount")
        if amount is None:
            amount = notice.get("amount_in_question") or notice.get("amount")
        try:
            amount = float(amount) if amount is not None else None
        except (TypeError, ValueError):
            amount = None
        source = str(facts.get("source") or "").lower()
        if source not in {"processing", "order", "other", "unknown"}:
            source = "unknown"
        return {**facts, "demand_amount": amount, "source": source}

    def get_questions(self, notice, locale="en", answers=None):
        facts = self._facts(notice)
        questions = [{
            "id": "demand_record_confirmed", "question_type": "single_choice",
            "text": {
                "en": "Do the demand amount and notice details match the official communication?",
                "hi": "क्या मांग राशि और सूचना विवरण आधिकारिक संचार से मेल खाते हैं?"
            },
            "help": {
                "en": "We need to confirm the record before preparing a payment or disagreement path.",
                "hi": "भुगतान या असहमति पथ तैयार करने से पहले हमें रिकॉर्ड की पुष्टि करने की आवश्यकता है।"
            },
            "options": [
                {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}}, 
                {"id": "no", "label": {"en": "No", "hi": "नहीं"}}, 
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
            ], 
            "required": True,
        }, {
            "id": "demand_status", "question_type": "single_choice",
            "text": {
                "en": "What is the current status of this demand?",
                "hi": "इस मांग की वर्तमान स्थिति क्या है?"
            },
            "help": {
                "en": "This determines whether the official next step is payment, challan evidence, or a disagreement response.",
                "hi": "यह तय करता है कि आधिकारिक अगला कदम भुगतान, चालान सबूत या असहमति प्रतिक्रिया है।"
            },
            "options": [
                {"id": "correct_unpaid", "label": {"en": "Correct and unpaid", "hi": "सही और अभी तक अवैतनित"}},
                {"id": "correct_paid", "label": {"en": "Correct but already paid", "hi": "सही लेकिन पहले से भुगतान किया गया"}},
                {"id": "disputed_full", "label": {"en": "Disagree fully", "hi": "पूरी तरह से असहमत"}},
                {"id": "disputed_partial", "label": {"en": "Disagree partially", "hi": "आंशिक रूप से असहमत"}},
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
            ], 
            "conditions": [{"depends_on": "demand_record_confirmed", "equals": "yes"}], 
            "required": True,
        }]
        if facts["source"] == "unknown":
            questions.append({
                "id": "demand_source", 
                "question_type": "single_choice", 
                "text": {
                    "en": "What appears to have caused this demand?",
                    "hi": "ऐसा प्रतीत होता है कि इस मांग का क्या कारण है?"
                },
                "help": {
                    "en": "The source helps identify which records to review; do not guess when the order or processing record is unclear.",
                    "hi": "स्रोत समीक्षा के लिए कौन से रिकॉर्ड की पहचान करने में मदद करता है; जब आदेश या प्रोसेसिंग रिकॉर्ड अस्पष्ट हो तो अनुमान न लगाएं।"
                },
                "options": [
                    {"id": "processing", "label": {"en": "Previous return processing", "hi": "पिछली रिटर्न प्रोसेसिंग"}}, 
                    {"id": "order", "label": {"en": "A previous assessment or other order", "hi": "पिछला आकलन या अन्य आदेश"}}, 
                    {"id": "other", "label": {"en": "Another department record", "hi": "अन्य विभागीय रिकॉर्ड"}}, 
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
                ], 
                "conditions": [{"depends_on": "demand_record_confirmed", "equals": "yes"}], 
                "required": True
            })
        questions.append({
            "id": "payment_evidence", 
            "question_type": "single_choice", 
            "text": {
                "en": "Do you have the payment challan or official payment record?",
                "hi": "क्या आपके पास भुगतान चालान या आधिकारिक भुगतान रिकॉर्ड है?"
            },
            "help": {
                "en": "This is needed only when payment is being claimed, not to decide whether the demand is correct.",
                "hi": "यह केवल तब आवश्यक है जब भुगतान का दावा किया जा रहा हो, यह तय करने के लिए नहीं कि मांग सही है या नहीं।"
            },
            "options": [
                {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}}, 
                {"id": "no", "label": {"en": "No", "hi": "नहीं"}}, 
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
            ], 
            "conditions": [{"depends_on": "demand_status", "equals": "correct_paid"}], 
            "required": True
        })
        questions.append({
            "id": "dispute_reasons", 
            "question_type": "multi_choice", 
            "text": {
                "en": "Why do you disagree with the demand?",
                "hi": "आप मांग से क्यों असहमत हैं?"
            },
            "help": {
                "en": "The official portal allows one or more reasons; choose only reasons supported by your records.",
                "hi": "आधिकारिक पोर्टल एक या अधिक कारणों की अनुमति देता है; केवल अपने रिकॉर्ड द्वारा समर्थित कारण चुनें।"
            },
            "options": [
                {"id": "already_paid", "label": {"en": "Demand already paid", "hi": "मांग पहले से भुगतान की गई"}}, 
                {"id": "previous_processing_error", "label": {"en": "Previous processing/order error", "hi": "पिछली प्रोसेसिंग/आदेश त्रुटि"}}, 
                {"id": "challan_credit_missing", "label": {"en": "Tax payment or challan not credited", "hi": "कर भुगतान या चालान क्रेडिट नहीं किया गया"}}, 
                {"id": "appeal_or_rectification_pending", "label": {"en": "Appeal or rectification is pending", "hi": "अपील या सुधार लंबित है"}}, 
                {"id": "other", "label": {"en": "Something else", "hi": "कुछ और"}}
            ], 
            "conditions": [{"depends_on": "demand_status", "one_of": ["disputed_full", "disputed_partial"]}], 
            "required": True
        })
        questions.append({
            "id": "undisputed_amount", 
            "question_type": "number", 
            "text": {
                "en": "What amount of the demand do you agree is payable?",
                "hi": "आप मांग की कितनी राशि देय स्वीकार करते हैं?"
            },
            "help": {
                "en": "For partial disagreement, the official guidance requires the undisputed portion to be paid before submitting the response.",
                "hi": "आंशिक असहमति के लिए, आधिकारिक मार्गदर्शन के अनुसार प्रतिक्रिया जमा करने से पहले विवादित नहीं वाली राशि का भुगतान करना आवश्यक है।"
            },
            "options": [], 
            "conditions": [{"depends_on": "demand_status", "equals": "disputed_partial"}], 
            "required": True
        })
        questions.append({
            "id": "dispute_details", 
            "question_type": "text", 
            "text": {
                "en": "Add the details supporting your disagreement.",
                "hi": "अपनी असहमति का समर्थन करने वाला विवरण जोड़ें।"
            },
            "help": {
                "en": "Use the notice, payment records, prior order or other documents. Tax Mitra will not add legal conclusions.",
                "hi": "सूचना, भुगतान रिकॉर्ड, पिछला आदेश या अन्य दस्तावेज़ का उपयोग करें। Tax Mitra कोई कानूनी निष्कर्ष नहीं जोड़ेगा।"
            },
            "options": [], 
            "conditions": [{"depends_on": "demand_status", "one_of": ["disputed_full", "disputed_partial"]}], 
            "required": True
        })
        
        # Localize the questions based on locale
        localized_questions = []
        for q in questions:
            localized_q = {
                "id": q["id"],
                "question_type": q["question_type"],
                "text": q["text"].get(locale, q["text"]["en"]),
                "help": q["help"].get(locale, q["help"]["en"]),
                "options": [{"id": opt["id"], "label": opt["label"].get(locale, opt["label"]["en"])} for opt in q["options"]],
                "required": q.get("required", False)
            }
            if "conditions" in q:
                localized_q["conditions"] = q["conditions"]
            localized_questions.append(localized_q)
        
        return {"questions": localized_questions, "facts": facts}

    def get_evidence(self, notice, statuses=None):
        statuses = statuses or {}
        return [
            {"request_id": "245-demand", "document_id": "245-notice", "document_name": {"en": "Latest outstanding-demand or section 245 notice", "hi": "नवीनतम बकाया मांग या धारा 245 सूचना"}, "reason": {"en": "It identifies the assessment year, demand reference and amount.", "hi": "इसमें निर्धारण वर्ष, मांग संदर्भ और राशि होती है।"}, "requirement_level": "required", "status": statuses.get("245-notice", "not_sure"), "source": [self.official_source]},
            {"request_id": "245-demand", "document_id": "245-payment-record", "document_name": {"en": "Challan/CIN or official payment record, if payment is claimed", "hi": "यदि भुगतान का दावा है तो चालान/CIN या आधिकारिक भुगतान रिकॉर्ड"}, "reason": {"en": "Use it to support an already-paid demand or tax-payment disagreement.", "hi": "पहले से भुगतान की गई मांग या कर भुगतान संबंधी असहमति के समर्थन के लिए।"}, "requirement_level": "possibly_relevant", "status": statuses.get("245-payment-record", "not_sure"), "source": [self.official_source]},
            {"request_id": "245-demand", "document_id": "245-supporting-records", "document_name": {"en": "Previous processing/order, rectification or appeal records", "hi": "पिछली प्रोसेसिंग/आदेश, सुधार या अपील रिकॉर्ड"}, "reason": {"en": "Use only the records that support the selected reason for disagreement.", "hi": "केवल चुने गए असहमति कारण के समर्थन वाले रिकॉर्ड रखें।"}, "requirement_level": "possibly_relevant", "status": statuses.get("245-supporting-records", "not_sure"), "source": [self.official_source]},
        ]

    def resolve(self, notice, answers, **kwargs):
        facts = self._facts(notice)
        if facts["demand_amount"] is None:
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The demand amount was not extracted safely; Tax Mitra will not calculate or invent it."}
        if answers.get("demand_record_confirmed") != "yes":
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The demand record was not confirmed against the official communication."}
        status = answers.get("demand_status")
        if status == "unsure" or not status:
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The demand status is uncertain; Tax Mitra will not choose payment or disagreement."}
        if status == "correct_unpaid":
            action = "The demand is marked correct and unpaid. Review the amount and use the official e-Pay Tax route; Tax Mitra will not initiate payment."
        elif status == "correct_paid":
            if answers.get("payment_evidence") != "yes":
                return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "Already-paid demand requires a confirmed challan or official payment record."}
            action = "The demand is marked correct and already paid. Review the challan/CIN details and submit the payment evidence through the official demand-response service."
        elif status in {"disputed_full", "disputed_partial"}:
            reasons = answers.get("dispute_reasons")
            if not isinstance(reasons, list) or not reasons or not str(answers.get("dispute_details") or "").strip():
                return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "A disagreement requires at least one selected reason and supporting details."}
            if status == "disputed_partial":
                try:
                    undisputed = float(answers.get("undisputed_amount"))
                except (TypeError, ValueError):
                    return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The undisputed amount must be entered before a partial disagreement can be prepared."}
                if undisputed <= 0 or undisputed >= facts["demand_amount"]:
                    return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The undisputed amount must be greater than zero and less than the extracted demand amount."}
                action = f"Prepare a partial disagreement for taxpayer review. The undisputed amount entered is {undisputed:g}; the official guidance requires that portion to be paid before submitting the response."
            else:
                action = "Prepare a full disagreement for taxpayer review using the selected reasons and details. No payment or legal conclusion has been generated."
        else:
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The demand status is not a supported response path."}
        return {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "demand_status": status, "action": action, "draft": f"Demand response action plan (review before use):\n{action}\n\nTax Mitra has not submitted a demand response or payment.", "checklist": self.get_evidence(notice), "next_step": "Review the response, evidence and any undisputed amount, then use Pending Actions > Response to Outstanding Demand on the official portal.", "handoff_allowed": False, "facts": facts, "portal_navigation_path": {"en": "Pending Actions → Response to Outstanding Demand", "hi": "Pending Actions → Response to Outstanding Demand"}}

    def generate_response(self, notice, answers, **kwargs): return self.resolve(notice, answers, **kwargs)
    def review(self, notice, answers, **kwargs): return {"status": "approved" if kwargs.get("approved") else "blocked", "handoff_allowed": False, "message": "Review is required before payment or demand response on the official portal."}


class InformationRequest1336Handler(WorkflowHandler):
    """Request-scoped response preparation for section 133(6) communications."""

    category = "scrutiny_information_133_6"
    official_source = "https://www.incometax.gov.in/iec/foportal/help/respond-to-e-proceedings"

    def _requests(self, notice: dict[str, Any]) -> list[dict[str, Any]]:
        raw = (notice.get("synthetic_extraction") or {}).get("requests") or notice.get("requests") or []
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            wording = str(item.get("original_text") or item.get("source_text") or item.get("text") or "").strip()
            if not wording:
                continue
            request_id = str(item.get("request_id") or item.get("id") or f"information-{index + 1}")
            explanation = item.get("plain_language_explanation") or item.get("explanation") or {"en": "Review the exact information requested and provide the records that support it."}
            if isinstance(explanation, str):
                explanation = {"en": explanation}
            evidence = item.get("required_evidence") or item.get("evidence") or []
            normalized.append({"id": request_id, "request_id": request_id, "technical_term": str(item.get("technical_term") or item.get("title") or wording[:120]), "original_text": wording, "plain_language_explanation": explanation, "page_number": item.get("page_number", item.get("page")), "source_location": item.get("source_location"), "confidence": float(item.get("confidence", 0.0)), "required_evidence": evidence if isinstance(evidence, list) else [], "status": str(item.get("status") or "not_started")})
        return normalized

    def get_questions(self, notice, locale="en", answers=None):
        requests = self._requests(notice)
        questions = [{
            "id": "information_record_confirmed", 
            "question_type": "single_choice", 
            "text": {
                "en": "Do these extracted requests match the 133(6) communication?",
                "hi": "क्या ये निकाले गए अनुरोध 133(6) संचार से मेल खाते हैं?"
            },
            "help": {
                "en": "We need to confirm the Department's exact requests before preparing any response.",
                "hi": "किसी भी प्रतिक्रिया तैयार करने से पहले हमें विभाग के सटीक अनुरोधों की पुष्टि करने की आवश्यकता है।"
            },
            "options": [
                {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}}, 
                {"id": "no", "label": {"en": "No", "hi": "नहीं"}}, 
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
            ], 
            "required": True
        }]
        for item in requests:
            questions.append({
                "id": f"information_status_{item['id']}", 
                "question_type": "single_choice", 
                "text": {
                    "en": f"How much of this request can you provide: {item['technical_term']}?",
                    "hi": f"आप इस अनुरोध का कितना हिस्सा प्रदान कर सकते हैं: {item['technical_term']}?"
                },
                "help": {
                    "en": "This determines whether the prepared response marks the request complete, partial, or unavailable. Not sure stays separate from unavailable.",
                    "hi": "यह तय करता है कि तैयार प्रतिक्रिया अनुरोध को पूर्ण, आंशिक या अनुपलब्ध के रूप में चिह्नित करती है। निश्चित नहीं अनुपलब्ध से अलग रहता है।"
                },
                "options": [
                    {"id": "complete", "label": {"en": "I can provide it", "hi": "मैं इसे प्रदान कर सकता हूँ"}}, 
                    {"id": "partial", "label": {"en": "I can provide some of it", "hi": "मैं इसका कुछ हिस्सा प्रदान कर सकता हूँ"}}, 
                    {"id": "unavailable", "label": {"en": "I cannot provide it", "hi": "मैं इसे प्रदान नहीं कर सकता"}}, 
                    {"id": "not_sure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}}
                ], 
                "conditions": [{"depends_on": "information_record_confirmed", "equals": "yes"}], 
                "required": True
            })
        
        # Localize the questions based on locale
        localized_questions = []
        for q in questions:
            localized_q = {
                "id": q["id"],
                "question_type": q["question_type"],
                "text": q["text"].get(locale, q["text"]["en"]),
                "help": q["help"].get(locale, q["help"]["en"]),
                "options": [{"id": opt["id"], "label": opt["label"].get(locale, opt["label"]["en"])} for opt in q["options"]],
                "required": q.get("required", False)
            }
            if "conditions" in q:
                localized_q["conditions"] = q["conditions"]
            localized_questions.append(localized_q)
        
        return {"questions": localized_questions, "requests": requests, "request_count": len(requests)}

    def get_evidence(self, notice, statuses=None):
        statuses = statuses or {}
        items: list[dict[str, Any]] = []
        for request in self._requests(notice):
            for index, document in enumerate(request["required_evidence"]):
                if isinstance(document, dict):
                    name = document.get("name") or document.get("document_name") or document.get("title") or "Supporting document"
                    reason = document.get("reason") or "Supports the information requested in the notice."
                    document_id = str(document.get("id") or document.get("document_id") or f"{request['id']}-evidence-{index + 1}")
                else:
                    name, reason, document_id = str(document), "Supports the information requested in the notice.", f"{request['id']}-evidence-{index + 1}"
                items.append({"request_id": request["id"], "document_id": document_id, "document_name": name, "reason": reason, "status": statuses.get(document_id, "not_sure"), "requirement_level": "required", "source": [self.official_source]})
        return items

    def resolve(self, notice, answers, **kwargs):
        requests = self._requests(notice)
        if not requests:
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "No specific 133(6) requests were extracted safely; Tax Mitra will not invent what to provide."}
        if answers.get("information_record_confirmed") != "yes":
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The extracted information requests were not confirmed against the communication."}
        prepared: list[dict[str, Any]] = []
        from app.workflows.notice_requests import extract_taxpayer_request_answer
        for item in requests:
            status = answers.get(f"information_status_{item['id']}")
            ans_pos, ans_details = extract_taxpayer_request_answer(item['id'], answers)
            if status not in {"complete", "partial", "unavailable", "not_sure"} and ans_pos:
                raw_choice = answers.get(f"notice_req_{item['id']}") or answers.get(item["id"])
                choice_str = raw_choice.get("choice") if isinstance(raw_choice, dict) else raw_choice
                status_map = {"provide": "complete", "partial": "partial", "not_applicable": "unavailable", "explain": "partial"}
                status = status_map.get(choice_str, "complete" if "complete" in ans_pos.lower() or "full" in ans_pos.lower() else "partial")
            if status not in {"complete", "partial", "unavailable", "not_sure"}:
                return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": f"The availability of request {item['id']} was not confirmed."}
            prepared.append({"request_id": item["id"], "technical_term": item["technical_term"], "original_text": item["original_text"], "plain_language_explanation": item["plain_language_explanation"], "page_number": item["page_number"], "confidence": item["confidence"], "availability": status, "taxpayer_position": ans_pos, "taxpayer_details": ans_details})
        uncertain = [item["request_id"] for item in prepared if item["availability"] == "not_sure"]
        action = "Prepare a structured 133(6) information response for taxpayer review, with each request answered separately and supporting attachments added where available."
        if uncertain:
            action += f" The following requests remain uncertain and must be resolved before submission: {', '.join(uncertain)}."
        from app.rules.letter_templates import format_formal_reply_letter
        draft_letter = format_formal_reply_letter(
            notice=notice,
            requests=requests,
            answers=answers,
            due_date=notice.get("deadline") or notice.get("response_deadline"),
        )
        return {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "requests": prepared, "response_plan": {"items": prepared, "partial_information_allowed": True}, "action": action, "draft": draft_letter, "checklist": self.get_evidence(notice), "deadline": notice.get("deadline") or notice.get("response_deadline"), "next_step": "Review every request and attachment, then use the official e-Proceedings or applicable Comply to Notice route. Tax Mitra will not submit.", "handoff_allowed": False, "portal_navigation_path": {"en": "e-Proceedings", "hi": "e-Proceedings"}}

    def generate_response(self, notice, answers, **kwargs): return self.resolve(notice, answers, **kwargs)
    def review(self, notice, answers, **kwargs): return {"status": "approved" if kwargs.get("approved") else "blocked", "handoff_allowed": False, "message": "Review is required before submitting the 133(6) response on the official portal."}


class AuthorityInformationRequestHandler(InformationRequest1336Handler):
    """Section-independent fallback for grounded AO/authority requests."""

    category = "authority_information_request"

    def get_questions(self, notice, locale="en", answers=None):
        result = super().get_questions(notice, locale, answers)
        if result.get("questions"):
            texts = {
                "en": "Do these extracted requests match the Income Tax authority communication?",
                "hi": "क्या ये निकाले गए अनुरोध आयकर प्राधिकरण संचार से मेल खाते हैं?",
            }
            helps = {
                "en": "We need to confirm the Department's exact requests before preparing any response.",
                "hi": "किसी भी प्रतिक्रिया तैयार करने से पहले हमें विभाग के सटीक अनुरोधों की पुष्टि करने की आवश्यकता है।",
            }
            result["questions"][0]["text"] = texts.get(locale, texts["en"])
            result["questions"][0]["help"] = helps.get(locale, helps["en"])
        return result

    def resolve(self, notice, answers, **kwargs):
        result = super().resolve(notice, answers, **kwargs)
        if result.get("status") == "supported":
            result["status"] = "partial_support"
            result["capability"] = "PARTIAL_SUPPORT"
            result["action"] = "Prepare a structured response to the Income Tax authority for taxpayer and professional review, answering each extracted request separately."
            result["draft"] = result["draft"].replace("133(6) information response plan", "Income Tax authority information response plan", 1)
            result["draft"] = result["draft"].replace("Prepare a structured 133(6) information response", result["action"], 1)
            uncertain = [item["request_id"] for item in result.get("requests", []) if item.get("availability") == "not_sure"]
            if uncertain:
                result["action"] += f" The following requests remain uncertain and must be resolved before submission: {', '.join(uncertain)}."
            result["next_step"] = "Review the authority, deadline, requests and attachments with a qualified professional where needed, then use the official e-Proceedings or applicable portal route. Tax Mitra will not submit."
            result["portal_navigation_path"] = {"en": "e-Proceedings", "hi": "e-Proceedings"}
        return result


class ClarificationHandler(AuthorityInformationRequestHandler):
    """Distinct clarification workflow sharing the generic request engine."""

    category = "ao_notice_clarification"

    def get_questions(self, notice, locale="en", answers=None):
        result = super().get_questions(notice, locale, answers)
        if result.get("questions"):
            texts = {
                "en": "Do these extracted clarification points match the communication?",
                "hi": "क्या ये निकाले गए स्पष्टीकरण बिंदु संचार से मेल खाते हैं?",
            }
            helps = {
                "en": "We need to confirm the exact point that the Department wants clarified before preparing remarks.",
                "hi": "टिप्पणी तैयार करने से पहले हमें यह पुष्टि करनी होगी कि विभाग किस बिंदु पर स्पष्टीकरण चाहता है।",
            }
            result["questions"][0]["text"] = texts.get(locale, texts["en"])
            result["questions"][0]["help"] = helps.get(locale, helps["en"])
        return result

    def resolve(self, notice, answers, **kwargs):
        result = super().resolve(notice, answers, **kwargs)
        if result.get("status") == "partial_support":
            result["status"] = "supported"
            result["capability"] = "SUPPORTED"
            result["action"] = "Prepare a concise clarification response for taxpayer review, addressing each clarification point with only the verified facts and supporting records."
            result["draft"] = result["draft"].replace("Income Tax authority information response plan", "Clarification response plan", 1)
            result["draft"] = result["draft"].replace("Prepare a structured response to the Income Tax authority", result["action"], 1)
            result["next_step"] = "Review the clarification, supporting records and deadline, then use the official e-Proceedings route. Tax Mitra will not submit."
            result["portal_navigation_path"] = {"en": "e-Proceedings", "hi": "e-Proceedings"}
        return result


class DefectiveReturn1399Handler(WorkflowHandler):
    """Grounded correction guidance for a defective-return notice.

    The Department's e-Proceedings flow requires the taxpayer to choose Agree
    or Disagree. Tax Mitra collects that position and prepares a reviewable
    action/remarks plan; it does not create an ITR JSON file or submit it.
    """

    category = "defective_return_139_9"
    official_source = "https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/prima%20facie%20adjustment-UM"

    def _requests(self, notice: dict[str, Any]) -> list[dict[str, Any]]:
        raw = (notice.get("synthetic_extraction") or {}).get("requests") or []
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(raw):
            text = str(item.get("original_text") or item.get("source_text") or "").strip()
            if not text:
                continue
            lower = text.lower()
            if "tds" in lower or "26as" in lower or "ais" in lower:
                title = "TDS or reported income mismatch"
                explanation = "Check that income corresponding to the TDS or reported receipt is included in the return."
                category = "tds_income_reporting"
            elif "balance sheet" in lower or "profit and loss" in lower or "p&l" in lower:
                title = "Business financial statements"
                explanation = "Check whether the return includes the business statements and schedules required for the income reported."
                category = "business_financial_statements"
            elif "name" in lower and "pan" in lower:
                title = "Name and PAN details"
                explanation = "Check that the name in the return matches the PAN record."
                category = "pan_name_mismatch"
            elif "nil" in lower or "zero" in lower or "tax liability" in lower:
                title = "Income and tax liability consistency"
                explanation = "Check that the income figures and the tax liability reported in the return are consistent."
                category = "income_tax_consistency"
            else:
                title = "Defect described in the notice"
                explanation = "Review the exact defect wording and correct only the return fields or schedules identified by the Department."
                category = "notice_specific_defect"
            request_id = str(item.get("request_id") or item.get("id") or f"defect-{index + 1}")
            normalized.append({
                "id": request_id,
                "request_id": request_id,
                "classification_id": category,
                "original_text": text,
                "what_department_is_asking": title,
                "plain_language_explanation": {"en": explanation},
                "why_required": {"en": "The Department identified this as a defect in the filed return or its schedules."},
                "required_evidence": [],
                "response_section": "Section 139(9)",
                "citations": [self.official_source],
                "confidence": float(item.get("confidence", 0.75)),
                "warnings": list(item.get("warnings", [])),
                "page_number": item.get("page_number", item.get("page")),
                "source_location": item.get("source_location"),
                "category": category,
                "status": item.get("status", "not_started"),
            })
        return normalized

    def get_questions(self, notice, locale="en", answers=None):
        requests = self._requests(notice)
        if not requests:
            return {"questions": [], "status": "safe_stop", "supported": False, "reason": "The notice was classified as 139(9), but no specific defect wording was extracted safely."}
        
        questions = [
            {
                "id": "defect_extraction_confirmed",
                "question_type": "single_choice",
                "text": {
                    "en": "Do these extracted defect details match your notice?",
                    "hi": "क्या ये निकाले गए दोष विवरण आपकी सूचना से मेल खाते हैं?"
                },
                "help": {
                    "en": "We need you to confirm the exact defect before Tax Mitra plans a correction path.",
                    "hi": "Tax Mitra सुधार पथ योजना बनाने से पहले हमें आपको सटीक दोष की पुष्टि करने की आवश्यकता है।"
                },
                "options": [
                    {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}},
                    {"id": "no", "label": {"en": "No", "hi": "नहीं"}},
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
                ],
                "required": True,
            },
            {
                "id": "defect_position",
                "question_type": "single_choice",
                "text": {
                    "en": "What is your position on the defect?",
                    "hi": "दोष पर आपकी स्थिति क्या है?"
                },
                "help": {
                    "en": "The official e-Proceedings flow asks you to agree with the defect or provide a reason for disagreeing.",
                    "hi": "आधिकारिक e-Proceedings प्रवाह आपसे दोष से सहमत होने या असहमति का कारण बताने के लिए कहता है।"
                },
                "options": [
                    {"id": "agree", "label": {"en": "Agree — I will correct the return", "hi": "सहमत — मैं रिटर्न को सुधारूँगा"}},
                    {"id": "disagree", "label": {"en": "Disagree — I want to explain why", "hi": "असहमत — मैं समझाना चाहता हूँ क्यों"}},
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
                ],
                "conditions": [{"depends_on": "defect_extraction_confirmed", "equals": "yes"}],
                "required": True,
            },
            {
                "id": "correction_route",
                "question_type": "single_choice",
                "text": {
                    "en": "How do you expect to correct the return?",
                    "hi": "आप रिटर्न को कैसे सुधारने की उम्मीद करते हैं?"
                },
                "help": {
                    "en": "This helps Tax Mitra show the appropriate official-portal action. It does not create or validate an ITR file.",
                    "hi": "यह Tax Mitra को उचित आधिकारिक पोर्टल कार्रवाई दिखाने में मदद करता है। यह ITR फ़ाइल नहीं बनाता या सत्यापित नहीं करता।"
                },
                "options": [
                    {"id": "online_correction", "label": {"en": "Correct the ITR online", "hi": "ITR को ऑनलाइन सुधारें"}},
                    {"id": "offline_json", "label": {"en": "Use the portal's offline response and applicable JSON", "hi": "पोर्टल की ऑफ़लाइन प्रतिक्रिया और लागू JSON का उपयोग करें"}},
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
                ],
                "conditions": [{"depends_on": "defect_position", "equals": "agree"}],
                "required": True,
            },
            {
                "id": "disagreement_reason",
                "question_type": "text",
                "text": {
                    "en": "Why do you disagree with the defect?",
                    "hi": "आप दोष से क्यों असहमत हैं?"
                },
                "help": {
                    "en": "The official flow asks you to write the reason for disagreement. Tax Mitra will use only the words you provide.",
                    "hi": "आधिकारिक प्रवाह आपसे असहमति का कारण लिखने के लिए कहता है। Tax Mitra केवल आपके द्वारा प्रदान किए गए शब्दों का उपयोग करेगा।"
                },
                "options": [],
                "conditions": [{"depends_on": "defect_position", "equals": "disagree"}],
                "required": True,
            },
        ]
        
        # Localize the questions based on locale
        localized_questions = []
        for q in questions:
            localized_q = {
                "id": q["id"],
                "question_type": q["question_type"],
                "text": q["text"].get(locale, q["text"]["en"]),
                "help": q["help"].get(locale, q["help"]["en"]),
                "options": [{"id": opt["id"], "label": opt["label"].get(locale, opt["label"]["en"])} for opt in q["options"]],
                "required": q.get("required", False)
            }
            if "conditions" in q:
                localized_q["conditions"] = q["conditions"]
            localized_questions.append(localized_q)
        
        return {
            "questions": localized_questions,
            "requests": requests,
            "request_count": len(requests),
        }

    def resolve(self, notice, answers, **kwargs):
        if answers.get("defect_extraction_confirmed") != "yes":
            return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The defect details were not confirmed against the original notice.", "answers": answers}
        position = answers.get("defect_position")
        if position == "agree":
            route = answers.get("correction_route")
            if route not in {"online_correction", "offline_json"}:
                return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "A correction route was not confirmed. Review the official portal or seek professional help before proceeding.", "answers": answers}
            route_label = "online ITR correction" if route == "online_correction" else "the portal's offline response with the applicable corrected JSON"
            draft = f"Correction action plan (review before use):\n1. Review each defect identified in the notice.\n2. Correct only the relevant return fields or schedules.\n3. Use {route_label}.\n4. Review the final response before submission.\n\nTax Mitra has not created or submitted an ITR file."
            from app.workflows.notice_requests import extract_taxpayer_request_answer
            itemized_defects = []
            for req in self._requests(notice):
                pos, det = extract_taxpayer_request_answer(req["id"], answers)
                if pos or det:
                    itemized_defects.append(f"- {req['what_department_is_asking']}: {pos}" + (f" (Details: {det})" if det else ""))
            if itemized_defects:
                draft += "\n\nItemized Defect Responses:\n" + "\n".join(itemized_defects)
            return {
                "supported": True,
                "status": "partial_support",
                "capability": "PARTIAL_SUPPORT",
                "workflow_id": self.category,
                "action": f"Review the identified defects, correct the return using {route_label}, and complete the response on the official e-Filing portal.",
                "draft": draft,
                "checklist": self._checklist(notice),
                "answers": answers,
                "handoff_allowed": False,
                "portal_navigation_path": {"en": "e-Proceedings", "hi": "e-Proceedings"},
            }
        if position == "disagree":
            reason = str(answers.get("disagreement_reason") or "").strip()
            if not reason:
                raise ValueError("A reason is required when disagreeing with the defect")
            draft = f"Remarks supplied by the taxpayer (review before use):\n{reason}\n\nTax Mitra has not added a legal conclusion or submitted these remarks."
            from app.workflows.notice_requests import extract_taxpayer_request_answer
            itemized_defects = []
            for req in self._requests(notice):
                pos, det = extract_taxpayer_request_answer(req["id"], answers)
                if pos or det:
                    itemized_defects.append(f"- {req['what_department_is_asking']}: {pos}" + (f" (Details: {det})" if det else ""))
            if itemized_defects:
                draft += "\n\nItemized Defect Responses:\n" + "\n".join(itemized_defects)
            return {
                "supported": True,
                "status": "partial_support",
                "capability": "PARTIAL_SUPPORT",
                "workflow_id": self.category,
                "action": "Review the taxpayer-provided disagreement remarks and submit them through the official e-Filing portal if correct.",
                "draft": draft,
                "checklist": self._checklist(notice),
                "answers": answers,
                "handoff_allowed": False,
                "portal_navigation_path": {"en": "e-Proceedings", "hi": "e-Proceedings"},
            }
        return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": "The taxpayer is not sure about the defect position; Tax Mitra will not choose Agree or Disagree.", "answers": answers}

    def get_evidence(self, notice, statuses=None):
        return [
            {"request_id": "defective-return", "document_id": "defective-return-notice", "document_name": {"en": "Original 139(9) notice"}, "reason": {"en": "Use the exact defect wording, deadline and notice reference."}, "requirement_level": "required", "status": "not_sure", "source": [self.official_source]},
            {"request_id": "defective-return", "document_id": "filed-return", "document_name": {"en": "Filed return and acknowledgement details"}, "reason": {"en": "Use these to locate and correct the return identified by the notice."}, "requirement_level": "required", "status": "not_sure", "source": [self.official_source]},
            {"request_id": "defective-return", "document_id": "corrected-itr-json", "document_name": {"en": "Applicable corrected ITR JSON, if the portal asks for offline response"}, "reason": {"en": "The official flow may require the applicable corrected JSON after agreeing with the defect."}, "requirement_level": "possibly_relevant", "status": "not_sure", "source": [self.official_source]},
        ]

    def _checklist(self, notice):
        return [{"id": item["document_id"], "title": item["document_name"], "why_needed": item["reason"]} for item in self.get_evidence(notice)]

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        approved = bool(kwargs.get("approved", False))
        return {"status": "approved" if approved else "blocked", "handoff_allowed": False, "message": "Review is required before using the official e-Filing portal."}


class IncomeIntimation143Handler(WorkflowHandler):
    """Guided handling for a final section 143(1) processing intimation.

    This is deliberately separate from 143(1)(a): there is no proposed
    adjustment response here. The handler explains the processed outcome and
    routes only to portal actions supported by the official CPC guidance.
    """

    category = "income_intimation_143_1"
    rectification_source = "https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/rectification-order-passed-cpc?mobile-app=1"
    mismatch_source = "https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/tax-credit-mismatch/tax-UM"
    refund_source = "https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/refund-reissue-UM"
    portal_source = "https://www.incometax.gov.in/iec/foportal/help/respond-to-e-proceedings"

    def _facts(self, notice: dict[str, Any]) -> dict[str, Any]:
        facts = notice.get("intimation_facts") or (notice.get("synthetic_extraction") or {}).get("intimation_facts") or {}
        outcome = str(facts.get("outcome") or "").lower()
        if outcome not in {"refund", "demand", "tax_difference", "tax_credit_mismatch", "no_action"}:
            # Uploaded sessions may only contain the normalized extracted text.
            # Infer an outcome only when the notice states an unambiguous
            # department result; amounts and legal conclusions remain absent.
            text = str(notice.get("official_text") or "").lower()
            if ("no demand" in text and "no refund" in text) or "no further action" in text:
                outcome = "no_action"
            elif re.search(r"tax\s+(?:credit\s+)?mismatch|tds\s+(?:credit\s+)?(?:differs|mismatch)|tcs\s+(?:credit\s+)?(?:differs|mismatch)", text):
                outcome = "tax_credit_mismatch"
            elif "refund" in text and not re.search(r"no\s+refund|refund\s+(?:not|failed)", text):
                outcome = "refund"
            elif re.search(r"demand\s+(?:payable|raised|due)|tax\s+payable", text):
                outcome = "demand"
            elif re.search(r"tax(?:\s+and\s+interest)?\s+(?:differs|difference|recomputed|computed differently)", text):
                outcome = "tax_difference"
            else:
                outcome = "unknown"
            return {**facts, "outcome": outcome, "discrepancies": []}
        discrepancies = [item for item in facts.get("discrepancies", []) if isinstance(item, dict)]
        return {**facts, "outcome": outcome, "discrepancies": discrepancies}

    def _unknown(self, message: str) -> dict[str, Any]:
        return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "reason": message}

    def get_questions(self, notice, locale="en", answers=None):
        facts = self._facts(notice)
        if facts.get("outcome") == "unknown":
            return {"questions": [], "status": "safe_stop", "supported": False, "reason": "The final 143(1) outcome was not extracted with enough confidence to plan an action."}
        questions = [{
            "id": "intimation_facts_confirmed",
            "question_type": "single_choice",
            "text": {
                "en": "Do these processed-return figures and outcome match your intimation?",
                "hi": "क्या ये संसाधित रिटर्न आंकड़े और परिणाम आपकी सूचना से मेल खाते हैं?",
            },
            "help": {
                "en": "We use your confirmation to avoid routing a refund, demand or correction action from an incorrect extraction.",
                "hi": "गलत निष्कर्षण से रिफंड, मांग या सुधार कार्रवाई से बचने के लिए हम आपकी पुष्टि का उपयोग करते हैं।",
            },
            "options": [
                {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}},
                {"id": "no", "label": {"en": "No", "hi": "नहीं"}},
                {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
            ],
            "required": True,
        }]
        if facts["outcome"] == "no_action":
            return {"questions": questions, "facts": facts, "outcome": facts["outcome"]}
        if facts["outcome"] == "refund":
            questions.append({
                "id": "refund_received",
                "question_type": "single_choice",
                "text": {
                    "en": "Have you received the refund shown in the intimation?",
                    "hi": "क्या आपको सूचना में दर्शाया गया रिफंड प्राप्त हो चुका है?",
                },
                "help": {
                    "en": "This determines whether the next step is simply to keep the record or to check the official refund-reissue service.",
                    "hi": "यह तय करता है कि अगला कदम केवल रिकॉर्ड रखना है या आधिकारिक रिफंड पुनः जारी सेवा की जांच करना है।",
                },
                "options": [
                    {"id": "yes", "label": {"en": "Yes", "hi": "हाँ"}},
                    {"id": "no", "label": {"en": "No", "hi": "नहीं"}},
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
                ],
                "conditions": [{"depends_on": "intimation_facts_confirmed", "equals": "yes"}],
                "required": True,
            })
        elif facts["outcome"] in {"demand", "tax_difference", "tax_credit_mismatch"}:
            questions.append({
                "id": "intimation_action",
                "question_type": "single_choice",
                "text": {
                    "en": "What best describes the action you want to review?",
                    "hi": "आप किस प्रकार की कार्रवाई की समीक्षा करना चाहते हैं?",
                },
                "help": {
                    "en": "A 143(1) intimation is already processed. This selects a review route; Tax Mitra will not decide whether the Department's figure is legally correct.",
                    "hi": "143(1) सूचना पहले से ही संसाधित है। यह समीक्षा मार्ग चुनता है; टैक्स मित्र यह तय नहीं करेगा कि विभागीय आंकड़ा कानूनी रूप से सही है या नहीं।",
                },
                "options": [
                    {"id": "accept", "label": {"en": "The processed result looks correct", "hi": "संसाधित परिणाम सही लगता है"}},
                    {"id": "rectification", "label": {"en": "There is a mistake apparent from the record", "hi": "रिकॉर्ड से स्पष्ट गलती दिखाई दे रही है"}},
                    {"id": "tax_credit", "label": {"en": "The issue is TDS/TCS or tax credit", "hi": "मुद्दा TDS/TCS या टैक्स क्रेडिट का है"}},
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
                ],
                "conditions": [{"depends_on": "intimation_facts_confirmed", "equals": "yes"}],
                "required": True,
            })
        return {"questions": questions, "facts": facts, "outcome": facts["outcome"], "request_count": len(facts.get("discrepancies", []))}

    def get_evidence(self, notice, statuses=None):
        facts = self._facts(notice)
        outcome = facts.get("outcome")
        recommendations = [{
            "request_id": "143-1-intimation",
            "document_id": "143-1-intimation-original",
            "document_name": {"en": "Original section 143(1) intimation", "hi": "धारा 143(1) की मूल सूचना"},
            "reason": {"en": "It contains the processed figures, reference number and outcome to be reviewed.", "hi": "इसमें प्रसंस्कृत आंकड़े, संदर्भ संख्या और परिणाम दिया होता है।"},
            "requirement_level": "required",
            "status": (statuses or {}).get("143-1-intimation-original", "not_sure"),
            "source": [self.rectification_source],
        }]
        if outcome in {"demand", "tax_difference", "refund"}:
            recommendations.append({
                "request_id": "143-1-intimation",
                "document_id": "143-1-filed-return",
                "document_name": {"en": "Filed return and computation", "hi": "दाखिल रिटर्न और गणना"},
                "reason": {"en": "Compare the return as filed with the CPC figures before choosing an action.", "hi": "कार्रवाई चुनने से पहले दाखिल रिटर्न की CPC आंकड़ों से तुलना करें।"},
                "requirement_level": "required",
                "status": (statuses or {}).get("143-1-filed-return", "not_sure"),
                "source": [self.rectification_source],
            })
        if outcome == "tax_credit_mismatch" or any("tds" in str(item).lower() or "tcs" in str(item).lower() for item in facts.get("discrepancies", [])):
            recommendations.append({
                "request_id": "143-1-intimation",
                "document_id": "143-1-tax-credit-records",
                "document_name": {"en": "Form 26AS/AIS and TDS/TCS or challan records", "hi": "फॉर्म 26AS/AIS और TDS/TCS या चालान रिकॉर्ड"},
                "reason": {"en": "Use these records to check whether the tax credit in the intimation matches the Department's records.", "hi": "इन रिकॉर्ड से जांचें कि सूचना में टैक्स क्रेडिट विभाग के रिकॉर्ड से मेल खाता है या नहीं।"},
                "requirement_level": "required",
                "status": (statuses or {}).get("143-1-tax-credit-records", "not_sure"),
                "source": [self.mismatch_source],
            })
        if outcome == "refund":
            recommendations.append({
                "request_id": "143-1-intimation",
                "document_id": "143-1-validated-bank-account",
                "document_name": {"en": "Validated bank-account details, if refund reissue is needed", "hi": "यदि रिफंड पुनः जारी करना हो तो सत्यापित बैंक खाता विवरण"},
                "reason": {"en": "The official refund-reissue service uses a validated bank account after a refund failure.", "hi": "आधिकारिक रिफंड पुनः जारी सेवा में रिफंड विफल होने के बाद सत्यापित बैंक खाते का उपयोग होता है।"},
                "requirement_level": "possibly_relevant",
                "status": (statuses or {}).get("143-1-validated-bank-account", "not_sure"),
                "source": [self.refund_source],
            })
        return recommendations

    def resolve(self, notice, answers, **kwargs):
        facts = self._facts(notice)
        if facts.get("outcome") == "unknown":
            return self._unknown("The final 143(1) outcome was not extracted safely.")
        if answers.get("intimation_facts_confirmed") != "yes":
            return self._unknown("The processed figures were not confirmed against the original intimation; Tax Mitra will not choose an action.")
        outcome = facts["outcome"]
        if outcome == "no_action":
            action = "No follow-up action was identified from the extracted intimation. Keep the intimation and filed-return records for your records."
            return {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "outcome": "no_action", "action": action, "draft": f"Action plan (review before use):\n{action}", "next_step": "No Tax Mitra response is prepared. Use the official portal only if the intimation itself identifies a later action.", "handoff_allowed": False, "facts": facts, "portal_navigation_path": {"en": "e-Proceedings", "hi": "e-Proceedings"}}
        if outcome == "refund":
            received = answers.get("refund_received")
            if received == "yes":
                action = "Keep the intimation and refund record. No response to the final 143(1) processing intimation is prepared."
            elif received == "no":
                action = "Review the official Refund Reissue service after confirming the refund failure and selecting a validated bank account."
            else:
                return self._unknown("You are not sure whether the refund was received; verify the bank and portal record before taking action.")
            return {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "outcome": outcome, "action": action, "draft": f"Action plan (review before use):\n{action}\n\nTax Mitra has not raised a refund request.", "next_step": "Review the official e-Filing portal record; Tax Mitra has not raised a refund request.", "handoff_allowed": False, "facts": facts, "checklist": self.get_evidence(notice), "portal_navigation_path": {"en": "e-Proceedings", "hi": "e-Proceedings"}}
        selected = answers.get("intimation_action")
        if selected == "accept":
            action = "The taxpayer indicated that the processed result looks correct. No dispute or rectification response is prepared."
            return {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "outcome": outcome, "action": action, "draft": f"Action plan (review before use):\n{action}", "next_step": "Retain the intimation and follow any payment or refund instruction shown on the official portal.", "handoff_allowed": False, "facts": facts, "portal_navigation_path": {"en": "e-Proceedings", "hi": "e-Proceedings"}}
        if selected == "rectification":
            return self._action_result(facts, "rectification", "Review a CPC rectification request for a mistake apparent from the record. Tax Mitra has not asserted that a mistake exists.", self.rectification_source, notice, {"en": "Services → Rectification", "hi": "Services → Rectification"})
        if selected == "tax_credit":
            return self._action_result(facts, "tax_credit_mismatch", "Review Tax Credit Mismatch Correction or rectification using the Department's tax-credit records. Tax Mitra has not changed or invented a credit.", self.mismatch_source, notice, {"en": "Services → Rectification", "hi": "Services → Rectification"})
        return self._unknown("You are not sure which follow-up applies; Tax Mitra will not choose between payment, rectification and tax-credit correction.")

    def _action_result(self, facts, action_id, action, source, notice, portal_navigation_path=None):
        result = {"supported": True, "status": "supported", "capability": "SUPPORTED", "workflow_id": self.category, "outcome": facts["outcome"], "path": {"path_id": action_id, "headline": action, "official_source": source}, "action": action, "draft": f"Action plan (review before use):\n{action}\n\nTax Mitra has not submitted anything to the Income Tax Department.", "next_step": "Review the official portal action and submit only after confirming the taxpayer's records.", "checklist": self.get_evidence(notice), "handoff_allowed": False, "facts": facts}
        if portal_navigation_path:
            result["portal_navigation_path"] = portal_navigation_path
        return result

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        approved = bool(kwargs.get("approved", False))
        return {"status": "approved" if approved else "blocked", "handoff_allowed": False, "message": "Review is required before using the official Income Tax portal."}


class SafeStopHandler(WorkflowHandler):
    category = "safe_stop"
    def _stop(self):
        return {"supported": False, "status": "safe_stop", "handoff_allowed": False, "message": "This workflow is not implemented safely yet."}
    def get_questions(self, notice, locale="en", answers=None): return {"questions": [], **self._stop()}
    def resolve(self, notice, answers, **kwargs): return self._stop()
    def get_evidence(self, notice, statuses=None): return []
    def generate_response(self, notice, answers, **kwargs): return self._stop()
    def review(self, notice, answers, **kwargs): return self._stop()


class GuidedPartialHandler(SafeStopHandler):
    """Grounded explanation/action guidance without unsafe legal drafting.

    Used for P0 workflows whose facts can be organized safely but whose final
    filing or legal position must remain with the taxpayer/professional.
    """
    def __init__(self, category: str):
        self.category = category

    def _requests(self, notice):
        return (notice.get("synthetic_extraction") or {}).get("requests") or []

    def get_questions(self, notice, locale="en", answers=None):
        if self.category == "defective_return_139_9" and not self._requests(notice):
            return {"questions": [], "status": "safe_stop", "supported": False, "reason": "No structured requests were extracted; confirm the notice before guidance."}
        title = "Does the extracted notice summary match your PDF?" if locale == "en" else "निकाले गए नोटिस का सारांश क्या आपके PDF से मेल खाता है?"
        return {"questions": [{"id": "notice_extraction_confirmed", "question_type": "confirmation", "text": title, "help": "We need your confirmation before using extracted facts.", "options": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}, {"id": "unsure", "label": "Not sure"}], "required": True}], "requests": self._requests(notice), "request_count": len(self._requests(notice))}

    def resolve(self, notice, answers, **kwargs):
        answer = answers.get("notice_extraction_confirmed")
        if answer != "yes":
            return {"supported": False, "status": "safe_stop", "reason": "The extracted facts must be confirmed before guidance can continue.", "answers": answers}
        requests = self._requests(notice)
        return {"supported": False, "status": "partial_support", "capability": "PARTIAL_SUPPORT", "workflow_id": self.category, "requests": requests, "missing": ["taxpayer-confirmed defect/figure details", "supporting records where the notice requires them"], "action": "Review the verified notice facts and complete the corresponding action on the official Income Tax e-Filing portal. Seek professional review if the legal position is disputed.", "answers": answers, "handoff_allowed": False}

    def get_evidence(self, notice, statuses=None):
        from app.evidence.mapping import map_evidence
        from app.extraction.notices import extract_notice_requests
        return map_evidence(extract_notice_requests(notice).requests, statuses)

    def generate_response(self, notice, answers, **kwargs):
        return self.resolve(notice, answers, **kwargs)

    def review(self, notice, answers, **kwargs):
        return {"status": "approved" if kwargs.get("approved") else "blocked", "handoff_allowed": False, "message": "Professional/taxpayer review is required; Tax Mitra does not submit this communication."}


class StructuredExplanationHandler(WorkflowHandler):
    """Useful explanation/preparation boundary for sensitive communications."""

    def __init__(self, category: str, capability: str = "EXPLANATION_ONLY"):
        self.category = category
        self.capability = capability

    def _facts(self, notice):
        extraction = notice.get("synthetic_extraction") or {}
        return {
            "section": notice.get("section"),
            "act_version": notice.get("act_version"),
            "assessment_year": notice.get("assessment_year"),
            "tax_year": notice.get("tax_year"),
            "deadline": notice.get("response_due_date") or notice.get("deadline") or notice.get("response_deadline"),
            "requests": extraction.get("requests") or [],
            "official_reference": notice.get("official_reference"),
        }

    def get_questions(self, notice, locale="en", answers=None):
        if self.category == "compliance_ais":
            return {"questions": [{
                "id": "compliance_issue_confirmed", "question_type": "single_choice",
                "text": {
                    "en": "What would you like to do with the reported information?",
                    "hi": "आप रिपोर्ट की गई जानकारी के साथ क्या करना चाहेंगे?",
                },
                "help": {
                    "en": "This selects an explanation and review path; Tax Mitra will not submit feedback.",
                    "hi": "यह व्याख्या और समीक्षा मार्ग चुनता है; टैक्स मित्र फीडबैक जमा नहीं करेगा।",
                },
                "options": [
                    {"id": "appears_correct", "label": {"en": "It appears correct", "hi": "यह सही प्रतीत होता है"}},
                    {"id": "need_feedback", "label": {"en": "I need to provide feedback", "hi": "मुझे फीडबैक देने की आवश्यकता है"}},
                    {"id": "not_mine", "label": {"en": "It does not belong to me", "hi": "यह मेरा नहीं है"}},
                    {"id": "unsure", "label": {"en": "Not sure", "hi": "मुझे पक्का नहीं है"}},
                ], "required": True,
            }], "facts": self._facts(notice)}
        return {"questions": [], "facts": self._facts(notice)}

    def resolve(self, notice, answers, **kwargs):
        facts = self._facts(notice)
        if self.category == "compliance_ais":
            choice = answers.get("compliance_issue_confirmed")
            if choice in {None, "unsure"}:
                return {"supported": False, "status": "safe_stop", "capability": "SAFE_STOP", "workflow_id": self.category, "reason": "The reported information needs taxpayer confirmation before a feedback path can be prepared.", "facts": facts, "handoff_allowed": False}
            action = "Review the AIS/e-Verification record and prepare feedback for taxpayer approval; Tax Mitra will not submit it." if choice != "appears_correct" else "Retain the AIS/compliance record and use the official portal only if a later action is required."
            return {"supported": False, "status": "partial_support", "capability": self.capability, "workflow_id": self.category, "action": action, "facts": facts, "handoff_allowed": False, "next_step": "Review the displayed record and use the official AIS or Compliance service after human approval."}
        return {"supported": False, "status": "safe_stop", "capability": self.capability, "workflow_id": self.category, "facts": facts, "requests": facts["requests"], "reason": "Tax Mitra can organize the extracted facts, but a qualified person should review the substantive response before any official action.", "next_step": "Review the communication, deadline and requested records with a qualified professional, then use the official portal.", "handoff_allowed": False}

    def get_evidence(self, notice, statuses=None):
        return [{"request_id": str(index), "document_id": f"{self.category}-{index}", "document_name": {"en": "Record or document mentioned in the communication", "hi": "संचार में उल्लिखित रिकॉर्ड या दस्तावेज़"}, "reason": {"en": "Use only evidence expressly connected to the extracted request.", "hi": "केवल निकाले गए अनुरोध से सीधे जुड़े प्रमाण का उपयोग करें।"}, "requirement_level": "possibly_relevant", "status": (statuses or {}).get(f"{self.category}-{index}", "not_sure")} for index, _ in enumerate(self._facts(notice)["requests"])]

    def generate_response(self, notice, answers, **kwargs): return self.resolve(notice, answers, **kwargs)
    def review(self, notice, answers, **kwargs): return {"status": "blocked", "handoff_allowed": False, "message": "Human or professional review is required before any official action."}


def get_workflow_handler(category: str | None) -> WorkflowHandler:
    handlers = {
        "income_mismatch_143_1a": IncomeMismatch143Handler(),
        "scrutiny_142_1": Scrutiny142Handler(),
        "defective_return_139_9": DefectiveReturn1399Handler(),
        "income_intimation_143_1": IncomeIntimation143Handler(),
        "rectification_154": Rectification154Handler(),
        "rectification_tax_credit_mismatch": TaxCreditMismatchHandler(),
        "tax_credit_tds_mismatch": TaxCreditMismatchHandler(),
        "demand_adjustment_245": Demand245Handler(),
        "outstanding_tax_demand": Demand245Handler(),
        "scrutiny_information_133_6": InformationRequest1336Handler(),
        "authority_information_request": AuthorityInformationRequestHandler(),
        "ao_notice_clarification": ClarificationHandler(),
        "authority_131": StructuredExplanationHandler("authority_131"),
        "compliance_ais": StructuredExplanationHandler("compliance_ais", "PARTIAL_SUPPORT"),
        "refund_communication": StructuredExplanationHandler("refund_communication"),
        "reassessment_148": StructuredExplanationHandler("reassessment_148"),
        "reassessment_148a": StructuredExplanationHandler("reassessment_148a"),
        "penalty_proceedings": StructuredExplanationHandler("penalty_proceedings"),
    }
    return handlers.get(category, SafeStopHandler())

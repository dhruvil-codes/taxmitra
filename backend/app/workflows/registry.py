"""Canonical Income Tax communication taxonomy and deterministic routing."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import re
from typing import Any


class WorkflowCapability(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL_SUPPORT = "PARTIAL_SUPPORT"
    EXPLANATION_ONLY = "EXPLANATION_ONLY"
    SAFE_STOP = "SAFE_STOP"


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    category: str
    title: dict[str, str]
    capability: WorkflowCapability
    classification_signals: tuple[str, ...]
    required_facts: tuple[str, ...]
    question_plan: str
    evidence: str
    response_action: str
    refusal_conditions: tuple[str, ...]
    implementation: str
    frontend_entry: str
    official_next_step: str = "Review any action on the official Income Tax e-Filing portal."

    @property
    def supported(self) -> bool:
        return self.capability is WorkflowCapability.SUPPORTED

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("classification_signals", "required_facts", "refusal_conditions"):
            data[key] = list(data[key])
        data["capability"] = self.capability.value
        data["supported"] = self.supported
        data["status"] = {
            WorkflowCapability.SUPPORTED: "supported",
            WorkflowCapability.PARTIAL_SUPPORT: "partial_support",
            WorkflowCapability.EXPLANATION_ONLY: "explanation_only",
            WorkflowCapability.SAFE_STOP: "safe_stop",
        }[self.capability]
        data["legacy_supported"] = self.supported
        return data


@dataclass(frozen=True)
class ClassificationResult:
    workflow_id: str
    category: str
    confidence: float
    grounding_status: str
    supported: bool
    status: str
    reason: str
    evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    capability: str = WorkflowCapability.SAFE_STOP.value

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"] = list(self.evidence)
        return data


def _w(workflow_id: str, category: str, title: dict[str, str], capability: WorkflowCapability,
       signals: tuple[str, ...], facts: tuple[str, ...], entry: str = "unsupported",
       implementation: str = "app.workflows.handlers", question_plan: str = "universal",
       evidence: str = "request-scoped evidence mapping", response: str = "explanation and safe routing") -> WorkflowDefinition:
    return WorkflowDefinition(workflow_id, category, title, capability, signals, facts, question_plan,
                              evidence, response, ("low extraction confidence", "ambiguous classification", "insufficient grounding"), implementation, entry)


_WORKFLOWS: tuple[WorkflowDefinition, ...] = (
    _w("defective_return_139_9", "defective_return_139_9", {"en": "139(9) defective return", "hi": "धारा 139(9) दोषपूर्ण रिटर्न"}, WorkflowCapability.PARTIAL_SUPPORT, ("139(9)", "defective return", "defect notice", "remove the defects"), ("notice section", "defect description", "correction deadline"), "journey", question_plan="universal defective-return plan", response="defect explanation, correction checklist, and taxpayer-controlled portal action"),
    _w("income_intimation_143_1", "income_intimation_143_1", {"en": "143(1) processing intimation", "hi": "धारा 143(1) प्रसंस्करण सूचना"}, WorkflowCapability.SUPPORTED, ("143(1)", "intimation under section 143", "processed return", "refund", "tax payable"), ("notice section", "assessment year", "tax/refund figures", "response or follow-up action"), "journey", question_plan="minimum intimation action plan", response="explain the processed figures and prepare a taxpayer-controlled follow-up action"),
    _w("income_mismatch_143_1a", "income_mismatch_143_1a", {"en": "143(1)(a) income mismatch", "hi": "धारा 143(1)(a) आय बेमेल"}, WorkflowCapability.SUPPORTED, ("143(1)(a)", "income mismatch", "adjustment proposed", "proposed adjustment"), ("notice section", "assessment year", "proposed adjustment", "taxpayer position"), "journey", "app.routers.workflow", "existing /api/workflow/questions", "existing 143(1)(a) checklist", "existing response path and human approval"),
    _w("scrutiny_142_1", "scrutiny_142_1", {"en": "142(1) scrutiny information request", "hi": "धारा 142(1) जांच सूचना अनुरोध"}, WorkflowCapability.SUPPORTED, ("142(1)", "annexure", "information and documents", "furnish the information"), ("notice section", "assessment year", "original requests", "response deadline"), "journey", "app.routers.scrutiny", "existing scrutiny minimum-question plan", "existing scrutiny evidence mapping", "existing response and human approval"),
    _w("scrutiny_information_133_6", "scrutiny_information_133_6", {"en": "133(6) information request", "hi": "धारा 133(6) सूचना अनुरोध"}, WorkflowCapability.SUPPORTED, ("133(6)", "section 133(6)", "information under section 133"), ("notice section", "requested information", "deadline"), "journey", question_plan="minimum information-request response plan", response="prepare a taxpayer-reviewed structured information response"),
    _w("authority_131", "authority_131", {"en": "Section 131 authority communication", "hi": "धारा 131 प्राधिकरण संचार"}, WorkflowCapability.EXPLANATION_ONLY, ("131", "section 131", "summons", "attendance before the assessing officer"), ("authority", "purpose", "deadline", "requests")),
    _w("compliance_ais", "compliance_ais", {"en": "AIS and compliance communication", "hi": "AIS और अनुपालन संचार"}, WorkflowCapability.PARTIAL_SUPPORT, ("annual information statement", "AIS", "e-campaign", "e-verification", "compliance portal", "SFT"), ("reported information", "taxpayer feedback", "deadline", "supporting records"), "journey", response="explain reported information and prepare taxpayer-reviewed feedback or portal action"),
    _w("authority_information_request", "authority_information_request", {"en": "Income Tax authority information request", "hi": "आयकर प्राधिकरण सूचना अनुरोध"}, WorkflowCapability.PARTIAL_SUPPORT, ("assessing officer", "income tax authority", "information request", "furnish information"), ("issuing authority", "purpose", "requested information", "deadline"), "journey", question_plan="minimum authority information-request plan", response="prepare a taxpayer-reviewed response where the extracted requests are sufficiently grounded"),
    _w("rectification_154", "rectification_154", {"en": "Section 154 rectification", "hi": "धारा 154 सुधार"}, WorkflowCapability.SUPPORTED, ("154", "section 154", "rectification"), ("notice section", "error or adjustment", "assessment year", "rectification type"), "journey", question_plan="minimum rectification eligibility plan", response="prepare a taxpayer-reviewed rectification route"),
    _w("rectification_tax_credit_mismatch", "rectification_tax_credit_mismatch", {"en": "Rectification or tax credit mismatch", "hi": "सुधार या कर क्रेडिट बेमेल"}, WorkflowCapability.SUPPORTED, ("rectification", "tax credit mismatch", "tds credit mismatch", "credit mismatch"), ("notice section", "mismatch or error", "assessment year", "supporting records"), "journey", question_plan="minimum tax-credit correction plan", response="prepare a taxpayer-reviewed tax-credit correction route"),
    _w("tax_credit_tds_mismatch", "tax_credit_tds_mismatch", {"en": "Tax credit / TDS mismatch", "hi": "कर क्रेडिट / TDS बेमेल"}, WorkflowCapability.SUPPORTED, ("tds mismatch", "tax credit mismatch", "form 26as", "ais mismatch"), ("assessment year", "credit mismatch", "supporting records", "credit type"), "journey", question_plan="minimum tax-credit correction plan", response="prepare a taxpayer-reviewed tax-credit correction or deductor follow-up"),
    _w("demand_adjustment_245", "demand_adjustment_245", {"en": "Section 245 demand adjustment", "hi": "धारा 245 मांग समायोजन"}, WorkflowCapability.SUPPORTED, ("245", "section 245", "adjustment against demand", "refund adjusted"), ("notice section", "outstanding demand", "refund", "deadline", "demand status"), "journey", question_plan="minimum demand response plan", response="prepare a taxpayer-reviewed demand response and payment/evidence route"),
    _w("outstanding_tax_demand", "outstanding_tax_demand", {"en": "Outstanding tax demand", "hi": "बकाया कर मांग"}, WorkflowCapability.SUPPORTED, ("outstanding demand", "tax demand", "demand notice"), ("demand amount", "assessment year", "payment or dispute status"), "journey", question_plan="minimum demand response plan", response="prepare a taxpayer-reviewed demand response and payment/evidence route"),
    _w("refund_communication", "refund_communication", {"en": "Refund communication", "hi": "रिफंड सूचना"}, WorkflowCapability.EXPLANATION_ONLY, ("refund communication", "refund status", "refund issued"), ("assessment year", "refund amount", "bank details")),
    _w("reassessment_148", "reassessment_148", {"en": "Section 148 reassessment", "hi": "धारा 148 पुनर्मूल्यांकन"}, WorkflowCapability.SAFE_STOP, ("148", "section 148", "reassessment"), ("notice section", "issue date", "response deadline")),
    _w("reassessment_148a", "reassessment_148a", {"en": "Section 148A proceedings", "hi": "धारा 148A कार्यवाही"}, WorkflowCapability.SAFE_STOP, ("148a", "section 148a", "show cause notice"), ("notice section", "issue date", "response deadline")),
    _w("penalty_proceedings", "penalty_proceedings", {"en": "Penalty proceedings", "hi": "दंड कार्यवाही"}, WorkflowCapability.SAFE_STOP, ("penalty", "show cause penalty", "imposition of penalty"), ("proceeding section", "allegation", "deadline")),
    _w("ao_notice_clarification", "ao_notice_clarification", {"en": "Assessing Officer clarification", "hi": "आकलन अधिकारी स्पष्टीकरण"}, WorkflowCapability.SUPPORTED, ("assessing officer", "ao notice", "clarification", "clarify the information"), ("issuing authority", "specific clarification requested", "response deadline"), "journey", question_plan="minimum clarification response plan", response="prepare a concise taxpayer-reviewed clarification response"),
    _w("unknown_income_tax_communication", "unknown_income_tax_communication", {"en": "Unknown Income Tax communication", "hi": "अज्ञात आयकर संचार"}, WorkflowCapability.SAFE_STOP, (), ("issuing authority", "dates", "requests")),
)
_BY_CATEGORY = {w.category: w for w in _WORKFLOWS}


def list_workflows() -> list[dict[str, Any]]:
    return [w.payload() for w in _WORKFLOWS]


def get_workflow(category_or_id: str | None) -> WorkflowDefinition | None:
    return _BY_CATEGORY.get(category_or_id or "")


def _text(notice: dict[str, Any]) -> str:
    values = [notice.get("section"), notice.get("issue_code"), notice.get("official_text"), notice.get("department_terminology")]
    for request in (notice.get("synthetic_extraction") or {}).get("requests") or []:
        values.extend([request.get("original_text"), request.get("response_section")])
    return "\n".join(str(v) for v in values if v).lower()


def _grounding_status(grounding: Any) -> str:
    if grounding is None: return "not_provided"
    get = grounding.get if isinstance(grounding, dict) else lambda k, default=None: getattr(grounding, k, default)
    below_floor = get("below_floor", None)
    if below_floor is True:
        return "below_floor"
    if below_floor is None and get("confidence") is not None and float(get("confidence")) < 0.7:
        return "below_floor"
    if get("verified") is False: return "pending"
    if get("verified") is True: return "verified"
    return "available"




def is_income_tax_communication(text: str) -> tuple[bool, float, list[str]]:
    """Determine if document is an authentic Income Tax Department communication."""
    normalized = text.lower()
    signals: list[str] = []
    strong_markers = (
        ("income tax department", "Income Tax Department header"),
        ("income-tax department", "Income-tax Department header"),
        ("आयकर विभाग", "Income Tax Department Hindi header"),
        ("government of india", "Government of India header"),
        ("govt. of india", "Govt. of India header"),
        ("govt of india", "Govt of India header"),
        ("भारत सरकार", "Government of India Hindi header"),
        ("central board of direct taxes", "CBDT"),
        ("cbdt", "CBDT"),
        ("national faceless assessment centre", "NFAC"),
        ("nfac", "NFAC"),
        ("ministry of finance", "Ministry of Finance"),
        ("वित्त मंत्रालय", "Ministry of Finance Hindi"),
        ("incometax.gov.in", "Official portal URL"),
        ("incometaxindia.gov.in", "Official portal URL"),
        ("itba/ast", "ITBA AST reference"),
        ("itba/com", "ITBA COM reference"),
        ("income-tax act, 1961", "Income-tax Act, 1961"),
        ("income tax act, 1961", "Income Tax Act, 1961"),
        ("income-tax act", "Income-tax Act"),
        ("income tax act", "Income Tax Act"),
        ("income tax act, 2025", "Income Tax Act, 2025"),
        ("आयकर अधिनियम", "Income Tax Act Hindi"),
    )
    for pattern, name in strong_markers:
        if pattern in normalized:
            signals.append(name)
    if re.search(r"\b(?:pan|permanent\s+account\s+number)\b", normalized, re.I):
        signals.append("PAN reference")
    if re.search(r"\b(?:din|document\s+identification\s+number)\b", normalized, re.I):
        signals.append("DIN reference")
    if re.search(r"\b(?:assessment\s+year|a\.y\.|ay\s*20\d\d)\b", normalized, re.I):
        signals.append("Assessment Year reference")
    if re.search(r"\b(?:assessing\s+officer|income\s+tax\s+officer|ward\s+\d+|circle\s+\d+|\bao\b)\b", normalized, re.I):
        signals.append("Assessing Officer / Ward")
    if re.search(r"\b(?:u/s|under\s+section|section)\s*(?:142|143|139|148|154|245|133|131)\b", normalized, re.I):
        signals.append("Statutory tax section reference")
    if re.search(r"\b[l1]ncome\s*[- ]?tax\b", normalized, re.I):
        signals.append("OCR Income Tax Department")
    if len(signals) >= 2 or any("header" in s or "Act" in s or "NFAC" in s or "Statutory" in s or "Assessing" in s for s in signals):
        confidence = min(0.99, 0.6 + len(signals) * 0.1)
        return True, confidence, signals
    return False, 0.0, signals


def _section_candidate(text: str) -> WorkflowDefinition | None:
    normalized = "".join(text.lower().split())
    if "143(1)(a)" in normalized or "143[1][a]" in normalized or "143(1)a" in normalized:
        return _BY_CATEGORY["income_mismatch_143_1a"]
    if "142(1)" in normalized or "142[1]" in normalized or "l42(1)" in normalized or "142(l)" in normalized or re.search(r"itba/ast/[a-z]/142\b", normalized):
        return _BY_CATEGORY["scrutiny_142_1"]
    if "139(9)" in normalized or "139[9]" in normalized:
        return _BY_CATEGORY["defective_return_139_9"]
    if "148a" in normalized or "148(a)" in normalized or "148[a]" in normalized or "148-a" in normalized:
        return _BY_CATEGORY["reassessment_148a"]
    if re.search(r"(?:section|u/s|under)148\b", normalized) or normalized.startswith("148") or "noticeundersection148" in normalized:
        return _BY_CATEGORY["reassessment_148"]
    if "133(6)" in normalized or "133[6]" in normalized:
        return _BY_CATEGORY["scrutiny_information_133_6"]
    if "131" in normalized and any(term in normalized for term in ("summons", "authority", "attendance", "assessingofficer")):
        return _BY_CATEGORY["authority_131"]
    if ("tds" in normalized or "tcs" in normalized or "26as" in normalized or "taxcredit" in normalized) and ("mismatch" in normalized or "credit" in normalized):
        return _BY_CATEGORY["tax_credit_tds_mismatch"]
    if "154" in normalized and ("rectif" in normalized or normalized.startswith("section154")):
        return _BY_CATEGORY["rectification_154"]
    if "section245" in normalized or "u/s245" in normalized or "under245" in normalized or normalized.startswith("245") or "adjustmentagainstdemand" in normalized:
        return _BY_CATEGORY["demand_adjustment_245"]
    if "143(1)" in normalized:
        return _BY_CATEGORY["income_intimation_143_1"]
    if any(term in normalized for term in ("annualinformationstatement", "e-campaign", "ecampaign", "e-verification", "everification", "complianceportal", "sftinformation")):
        return _BY_CATEGORY["compliance_ais"]
    if "clarification" in normalized and ("assessingofficer" in normalized or "incometaxauthority" in normalized):
        return _BY_CATEGORY["ao_notice_clarification"]
    if ("assessingofficer" in normalized or "incometaxauthority" in normalized) and any(term in normalized for term in ("informationrequest", "furnishinformation", "provideinformation", "documentsrequested")):
        return _BY_CATEGORY["authority_information_request"]
    if "penalty" in normalized or "270a" in normalized or "271" in normalized:
        return _BY_CATEGORY["penalty_proceedings"]
    if "refund" in normalized and not any(term in normalized for term in ("143(1)", "intimation", "demand")):
        return _BY_CATEGORY["refund_communication"]
    return None


def classify_extracted_notice(notice: dict[str, Any], grounding: Any = None) -> ClassificationResult:
    content = _text(notice)
    raw_text = str(notice.get("official_text") or content)
    candidate = _section_candidate(content) or _section_candidate(raw_text)
    is_tax, tax_conf, tax_signals = is_income_tax_communication(raw_text)
    if candidate is not None:
        is_tax = True
    grounding_status = _grounding_status(grounding)

    is_explicit_non_tax = str(notice.get("section") or "").strip().upper() == "NON_TAX" or "non-tax" in raw_text.lower() or "not a tax" in raw_text.lower()
    if is_explicit_non_tax or (not is_tax and not notice.get("section") and candidate is None):
        return ClassificationResult(
            "not_income_tax_document", "not_income_tax_document", 0.0,
            grounding_status, False, "safe_stop",
            "the uploaded document was not recognized as an Indian Income Tax Department communication",
            (), WorkflowCapability.SAFE_STOP.value
        )



    section_value = "".join(str(notice.get("section") or "").lower().split())
    if section_value in {"139(9)", "143(1)", "143(1)(a)", "142(1)", "133(6)", "154", "245", "148", "148a", "148(a)", "131"}:
        content = f"section{section_value} {content}"
    selected = candidate or _section_candidate(content)
    evidence: list[dict[str, Any]] = []
    if selected:
        evidence.append({"kind": "section_reference", "value": selected.classification_signals[0], "source": "extracted_text"})
        if selected.category == "income_intimation_143_1" and any(s in content for s in ("adjustment", "proposed")):
            selected = _BY_CATEGORY["income_mismatch_143_1a"]
            evidence.append({"kind": "structural_signal", "value": "proposed adjustment", "source": "extracted_text"})
        confidence, reason = (0.98, "explicit section reference with corroborating notice language") if len(evidence) > 1 else (1.0, "explicit section reference")
    else:
        scored = sorted(((sum(1 for signal in w.classification_signals if signal in content), w) for w in _WORKFLOWS if w.classification_signals), key=lambda x: x[0], reverse=True)
        top = scored[0][0] if scored else 0
        tied = [w for score, w in scored if score == top and score > 0]
        if not tied:
            evidence.extend({"kind": "tax_signal", "value": s} for s in tax_signals)
            return ClassificationResult(
                "unknown_income_tax_communication", "unknown_income_tax_communication",
                tax_conf if is_tax else 0.0, grounding_status, False, "safe_stop",
                "identified as an Income Tax communication, but the specific proceeding is not currently supported for guided response",
                tuple(evidence), WorkflowCapability.SAFE_STOP.value
            )
        if len(tied) > 1:
            return ClassificationResult("ambiguous", "ambiguous", 0.0, grounding_status, False, "safe_stop", "more than one registered workflow matched the extracted communication", tuple({"kind": "competing_signal", "value": w.category} for w in tied), WorkflowCapability.SAFE_STOP.value)
        selected, confidence, reason = tied[0], min(0.85, 0.55 + 0.1 * top), "department terminology and structural content signals"
        evidence.extend({"kind": "terminology", "value": s, "source": "extracted_text"} for s in selected.classification_signals if s in content)
    if grounding_status == "below_floor":
        return ClassificationResult(selected.workflow_id, selected.category, confidence, grounding_status, False, "safe_stop", "classification grounding is below the safe floor", tuple(evidence), selected.capability.value)
    if confidence < 0.7:
        return ClassificationResult(selected.workflow_id, selected.category, confidence, grounding_status, False, "safe_stop", "classification confidence is too low to route safely", tuple(evidence), selected.capability.value)
    if selected.capability is WorkflowCapability.SAFE_STOP:
        return ClassificationResult(selected.workflow_id, selected.category, confidence, grounding_status, False, "safe_stop", "communication is legally sensitive or not safe to automate", tuple(evidence), selected.capability.value)
    if selected.capability is WorkflowCapability.EXPLANATION_ONLY:
        return ClassificationResult(selected.workflow_id, selected.category, confidence, grounding_status, False, "safe_stop", "explanation is available but a guided response is not safe to automate", tuple(evidence), selected.capability.value)
    if selected.category in {"defective_return_139_9", "authority_information_request", "ao_notice_clarification"} and not (notice.get("synthetic_extraction") or {}).get("requests"):
        return ClassificationResult(selected.workflow_id, selected.category, confidence, grounding_status, False, "safe_stop", "notice facts require confirmation before partial guidance can begin", tuple(evidence), selected.capability.value)
    return ClassificationResult(selected.workflow_id, selected.category, confidence, grounding_status, selected.supported, "supported" if selected.supported else "partial_support", reason, tuple(evidence), selected.capability.value)


def classify_ai_proposal(notice: dict[str, Any], proposal: dict[str, Any], grounding: Any = None) -> ClassificationResult:
    """Validate an AI identification proposal through the canonical registry."""
    grounding_status = _grounding_status(grounding)
    evidence = tuple(item for item in proposal.get("evidence", ()) if isinstance(item, dict))
    category = str(proposal.get("category") or "unknown_income_tax_communication")
    is_income_tax = proposal.get("is_income_tax_communication")
    if is_income_tax is False and category != "unknown_income_tax_communication":
        return ClassificationResult(
            "not_income_tax_document", "not_income_tax_document", 1.0,
            grounding_status, False, "safe_stop", "the uploaded document was not identified as an Indian Income Tax Department communication",
            evidence, WorkflowCapability.SAFE_STOP.value,
        )
    if category == "unknown_income_tax_communication" and proposal.get("is_income_tax_communication") is True:
        proposal_text = " ".join(str(proposal.get(key) or "") for key in ("authority", "authority_type", "communication_type", "purpose", "reason")) .lower()
        if "clarif" in proposal_text and ("assessing officer" in proposal_text or "income tax authority" in proposal_text or "ao" in proposal_text):
            category = "ao_notice_clarification"
        elif ("assessing officer" in proposal_text or "income tax authority" in proposal_text or "ao" in proposal_text) and any(term in proposal_text for term in ("information", "document", "furnish", "provide")):
            category = "authority_information_request"
    selected = get_workflow(category)
    try:
        confidence = max(0.0, min(1.0, float(proposal.get("confidence", 0.0))))
    except (TypeError, ValueError):
        confidence = 0.0
    if selected is None:
        selected = _BY_CATEGORY["unknown_income_tax_communication"]
        category = selected.category
        confidence = min(confidence, 0.45)
    reason = str(proposal.get("reason") or "classification based on extracted communication evidence")
    if proposal.get("section") and not any(item.get("kind") == "section_reference" for item in evidence):
        evidence += ({"kind": "section_reference", "value": proposal["section"], "source": "openai_extracted_text"},)
    if grounding_status == "below_floor" or confidence < 0.7:
        return ClassificationResult(selected.workflow_id, category, confidence, grounding_status, False, "safe_stop", "classification confidence or extraction grounding is too low to route safely", evidence, selected.capability.value)
    if selected.capability is WorkflowCapability.SAFE_STOP:
        return ClassificationResult(selected.workflow_id, category, confidence, grounding_status, False, "safe_stop", selected.refusal_conditions[0], evidence, selected.capability.value)
    if selected.capability is WorkflowCapability.EXPLANATION_ONLY:
        return ClassificationResult(selected.workflow_id, category, confidence, grounding_status, False, "explanation_only", reason, evidence, selected.capability.value)
    if selected.capability is WorkflowCapability.PARTIAL_SUPPORT:
        return ClassificationResult(selected.workflow_id, category, confidence, grounding_status, False, "partial_support", reason, evidence, selected.capability.value)
    return ClassificationResult(selected.workflow_id, category, confidence, grounding_status, True, "supported", reason, evidence, selected.capability.value)

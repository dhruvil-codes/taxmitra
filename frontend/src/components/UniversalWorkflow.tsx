import { EvidenceRecommendation, NoticeCard, Question, QuestionAnswer, ScrutinyRequest, WorkflowCapability } from "../lib";
import { PrimaryButton } from "../components";

const pick = (value: Record<string, string> | undefined, locale: string) => value?.[locale] ?? value?.en ?? "";

export function CapabilityBadge({ capability, locale }: { capability: WorkflowCapability; locale: string }) {
  const labels: Record<WorkflowCapability, Record<string, string>> = { SUPPORTED: { en: "Guided workflow", hi: "निर्देशित कार्यप्रवाह" }, PARTIAL_SUPPORT: { en: "Guided with a safe boundary", hi: "सुरक्षित सीमा के साथ मार्गदर्शन" }, EXPLANATION_ONLY: { en: "Explanation and next steps", hi: "व्याख्या और अगले कदम" }, SAFE_STOP: { en: "Safe stop", hi: "सुरक्षित रोक" } };
  return <span className={`capability-badge capability-${capability.toLowerCase()}`}>{labels[capability][locale] ?? labels[capability].en}</span>;
}

type ContractExplanationProps = {
  capability: WorkflowCapability;
  title: string;
  reason: string;
  notice?: NoticeCard;
  requests: ScrutinyRequest[];
  nextSteps: string[];
  originalText?: string;
  locale: string;
};

const requestTitle = (request: ScrutinyRequest, index: number) =>
  request.what_department_is_asking || request.response_section || request.category || `Request ${index + 1}`;

const requestExplanation = (request: ScrutinyRequest, locale: string) =>
  pick(request.plain_language_explanation, locale) ||
  pick(request.why_required, locale) ||
  (locale === "hi" ? "इस अनुरोध के लिए मूल शब्द देखें।" : "See the original wording for the exact request.");

function deadlineText(notice: NoticeCard | undefined, locale: string) {
  if (!notice?.due_date) return locale === "hi" ? "समय सीमा स्पष्ट रूप से नहीं मिली।" : "No clear deadline was identified.";
  const date = new Date(`${notice.due_date}T00:00:00`);
  const formatted = Number.isNaN(date.getTime()) ? notice.due_date : date.toLocaleDateString(locale === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "long", year: "numeric" });
  return locale === "hi" ? `${formatted} तक जवाब दें।` : `Respond by ${formatted}.`;
}

export function ContractExplanation({ capability, title, reason, notice, requests, nextSteps, originalText, locale }: ContractExplanationProps) {
  const safe = capability === "SAFE_STOP";
  const explanation = safe
    ? (locale === "hi" ? "Tax Mitra ने संचार को समझने की कोशिश की, लेकिन सुरक्षित रूप से आगे बढ़ने के लिए पर्याप्त निश्चितता नहीं है।" : "Tax Mitra identified this communication, but does not have enough certainty to guide a response safely.")
    : capability === "EXPLANATION_ONLY"
      ? (locale === "hi" ? "यह संचार समझाया जा सकता है, लेकिन Tax Mitra इसकी ओर से उत्तर तैयार नहीं करेगा।" : "This communication can be explained, but Tax Mitra will not prepare a response for it.")
      : (locale === "hi" ? "यह संचार क्या कहता है और आपके अगले कदम क्या हो सकते हैं, उसका संक्षिप्त सार नीचे है।" : "Here is a concise summary of what this communication says and what may happen next.");
  return <section className="universal-section contract-explanation" aria-labelledby="what-we-found-heading">
    <p className="contract-kicker">{locale === "hi" ? "संचार का सार" : "Communication summary"}</p>
    <h2 id="what-we-found-heading" className="question-title">{locale === "hi" ? "आपके नोटिस का मतलब" : "What this notice means"}</h2>
    <p className="app-lead">{title}</p>
    <p className="app-body">{explanation}</p>

    <div className="contract-summary-grid">
      <div><h3>{locale === "hi" ? "विभाग क्या चाहता है" : "What the Department wants"}</h3><p>{requests.length ? (locale === "hi" ? `इस नोटिस में ${requests.length} अनुरोध मिले हैं।` : `This notice contains ${requests.length} request${requests.length === 1 ? "" : "s"}.`) : reason}</p></div>
      <div><h3>{locale === "hi" ? "समय सीमा" : "Deadline"}</h3><p>{deadlineText(notice, locale)}</p></div>
    </div>

    {requests.length > 0 && <div className="contract-request-summary"><h3>{locale === "hi" ? "हर अनुरोध" : "Each request"}</h3><ol>{requests.map((request, index) => <li key={request.request_id || request.id || index}><div><strong>{requestTitle(request, index)}</strong><p>{requestExplanation(request, locale)}</p><small>{request.source_location || (request.page_number ? (locale === "hi" ? `पृष्ठ ${request.page_number}` : `Page ${request.page_number}`) : "")}</small></div></li>)}</ol></div>}

    {nextSteps.length > 0 && <div className="contract-next-step"><h3>{locale === "hi" ? "इसके बाद क्या होगा" : "What happens next"}</h3><ul>{nextSteps.map((step) => <li key={step}>{step}</li>)}</ul></div>}
    <div className="contract-help"><h3>{locale === "hi" ? "Tax Mitra किसमें मदद कर सकता है" : "What Tax Mitra can help with"}</h3><p>{safe || capability === "EXPLANATION_ONLY" ? (locale === "hi" ? "संचार, उपलब्ध तथ्यों और संभावित अगले कदमों को समझाना।" : "Explain the communication, available facts, and grounded next steps.") : (locale === "hi" ? "अनुरोधों को समझना, ज़रूरी जानकारी व्यवस्थित करना और समीक्षा के लिए तैयार करना।" : "Understand requests, organize the needed information, and prepare it for your review.")}</p></div>
    {originalText && <details className="contract-original"><summary>{locale === "hi" ? "मूल नोटिस की भाषा देखें" : "View original notice wording"}</summary><blockquote>{originalText}</blockquote></details>}
  </section>;
}

type ContractQuestionProps = {
  question: Question;
  locale: string;
  value: QuestionAnswer | undefined;
  onChange: (value: QuestionAnswer) => void;
  onContinue: () => void;
};

const canonicalQuestionType = (type: Question["question_type"]): NonNullable<Question["question_type"]> => {
  if (type === "multiple_choice") return "multi_choice";
  if (type === "free_text") return "text";
  return type ?? "text";
};

export function ContractQuestion({ question, locale, value, onChange, onContinue }: ContractQuestionProps) {
  const type = canonicalQuestionType(question.question_type);
  const selected: string[] = Array.isArray(value) ? value.map(String) : value && typeof value === "object" ? [value.choice] : value !== undefined && value !== "" ? [String(value)] : [];
  const otherSelected = selected.some((item) => /(^|[_-])(other|something_else)([_-]|$)/i.test(item));
  const textValue = value && typeof value === "object" && !Array.isArray(value) ? value.other : "";
  const setSingle = (option: string) => {
    if (type === "choice_with_other" && /(^|[_-])(other|something_else)([_-]|$)/i.test(option)) onChange({ choice: option, other: "" });
    else onChange(option);
  };
  const toggle = (option: string) => onChange(selected.includes(option) ? selected.filter((item) => item !== option) : [...selected, option]);
  const needsValue = type === "multi_choice" ? selected.length > 0 : type === "choice_with_other" ? (otherSelected ? textValue.trim().length > 0 : selected.length > 0) : Boolean(value);
  if (type === "text" || type === "number" || type === "date") return <div className="contract-question-fields"><label htmlFor={`question-${question.id}`}>{type === "text" ? "Your answer" : type === "number" ? "Enter a number" : "Select a date"}</label>{type === "text" ? <textarea id={`question-${question.id}`} aria-label={question.text} className="w-full border border-slate-300 p-4" rows={5} value={typeof value === "string" ? value : ""} onChange={(event) => onChange(event.target.value)} /> : <input id={`question-${question.id}`} aria-label={question.text} className="w-full border border-slate-300 p-4" type={type} value={typeof value === "string" ? value : ""} onChange={(event) => onChange(event.target.value)} />}<PrimaryButton onClick={onContinue}>Continue</PrimaryButton></div>;
  return <div className="contract-question-fields"><div className={type === "multi_choice" ? "answer-grid answer-grid-multi" : "answer-grid"}>{question.options.map((option) => <label className="journey-answer" key={option.id}><input type={type === "multi_choice" ? "checkbox" : "radio"} name={`question-${question.id}`} checked={selected.includes(option.id)} onChange={() => type === "multi_choice" ? toggle(option.id) : setSingle(option.id)} /><span>{option.label}</span></label>)}</div>{type === "choice_with_other" && otherSelected && <label className="contract-other-field" htmlFor={`question-${question.id}-other`}>Tell us briefly what you mean<textarea id={`question-${question.id}-other`} aria-label="Something else" rows={4} value={textValue} onChange={(event) => onChange({ choice: selected[0] ?? "something_else", other: event.target.value })} /></label>}<PrimaryButton disabled={!needsValue} onClick={onContinue}>Continue</PrimaryButton></div>;
}

export function ContractRequests({ requests, locale }: { requests: ScrutinyRequest[]; locale: string }) {
  if (!requests.length) return null;
  return <section className="universal-section" aria-labelledby="notice-requests-heading"><p className="contract-kicker">{locale === "hi" ? "नोटिस के अनुरोध" : "Requests in this notice"}</p><h2 id="notice-requests-heading" className="question-title">{locale === "hi" ? "विभाग क्या मांग रहा है" : "What the Department is asking"}</h2><div className="universal-request-list">{requests.map((request, index) => <article className="universal-request" key={request.request_id || request.id || index}><div className="universal-request-number">{String(index + 1).padStart(2, "0")}</div><div><p className="app-section-label">{request.category || request.response_section || "Notice request"}</p><h3>{requestTitle(request, index)}</h3><p className="app-body">{requestExplanation(request, locale)}</p><details><summary>{locale === "hi" ? "मूल शब्द और स्रोत" : "View original notice wording"}</summary><blockquote>{request.original_text}</blockquote><p className="app-caption">{request.source_location || (request.page_number ? `Page ${request.page_number}` : "Source page not identified")}</p></details></div></article>)}</div></section>;
}

export function ContractEvidence({ evidence, locale }: { evidence: EvidenceRecommendation[]; locale: string }) {
  if (!evidence.length) return null;
  return <section className="universal-section" aria-labelledby="evidence-heading"><p className="contract-kicker">{locale === "hi" ? "तैयारी" : "Preparation"}</p><h2 id="evidence-heading" className="question-title">{locale === "hi" ? "क्या तैयार रखना है" : "What you may need"}</h2><div className="universal-evidence-list">{evidence.map((item) => <article className="universal-evidence" key={item.document_id}><div><h3>{pick(item.document_name, locale)}</h3><p>{pick(item.reason, locale)}</p><small>{item.requirement_level === "required" ? (locale === "hi" ? "नोटिस में आवश्यक" : "Required by the notice") : (locale === "hi" ? "संभवतः प्रासंगिक" : "Possibly relevant")}</small></div></article>)}</div></section>;
}

export function CapabilityBoundary({ capability, reason, nextSteps, locale }: { capability: WorkflowCapability; reason: string; nextSteps: string[]; locale: string }) {
  const partial = capability === "PARTIAL_SUPPORT";
  const explanation = capability === "EXPLANATION_ONLY" ? (locale === "hi" ? "Tax Mitra इस संचार को समझाने और अगले कदम दिखाने में मदद कर सकता है, लेकिन अभी सुरक्षित उत्तर तैयार नहीं कर सकता।" : "Tax Mitra can explain this communication and show next steps, but cannot safely prepare the response yet.") : partial ? (locale === "hi" ? "Tax Mitra अनुरोधों को समझने और जानकारी व्यवस्थित करने में मदद कर सकता है, लेकिन कानूनी उत्तर का मसौदा तैयार नहीं करेगा।" : "Tax Mitra can help you understand the requests and organize information, but will not draft an unsupported legal response.") : (locale === "hi" ? "Tax Mitra सुरक्षित सीमा पर रुक गया है और कोई अनुमानित कानूनी निष्कर्ष या उत्तर नहीं बनाया है।" : "Tax Mitra has stopped at a safe boundary and has not invented a legal conclusion or response.");
  const label = capability === "EXPLANATION_ONLY" ? "EXPLANATION ONLY" : partial ? "PARTIAL SUPPORT" : "SAFE STOP";
  return <section className="universal-boundary" role="status"><p className="contract-kicker">{locale === "hi" ? "सुरक्षित सीमा" : label === "EXPLANATION ONLY" ? "Explanation boundary" : partial ? "Partial support boundary" : "Safe stop"}</p><h2>{locale === "hi" ? "आपके लिए इसका क्या अर्थ है" : "What this means for you"}</h2><p className="app-body">{explanation}</p><div className="notice-boundary"><strong>{locale === "hi" ? "Tax Mitra ने क्या पाया" : "What Tax Mitra found"}</strong><p>{reason}</p></div><div className="notice-boundary"><strong>{locale === "hi" ? "Tax Mitra क्या कर सकता है" : "What Tax Mitra can help with"}</strong><p>{capability === "EXPLANATION_ONLY" ? (locale === "hi" ? "संचार, अनुरोध और संभावित अगले कदम समझाना।" : "Explain the communication, requests, and grounded next steps.") : (locale === "hi" ? "निकाले गए तथ्यों और अगले कदम को दिखाना।" : "Show grounded facts and supported next steps.")}</p></div><div className="notice-boundary"><strong>{locale === "hi" ? "Tax Mitra क्या सुरक्षित रूप से नहीं कर सकता" : "What Tax Mitra cannot safely do"}</strong><p>{explanation}</p></div>{nextSteps.length > 0 && <div><strong>{locale === "hi" ? "अगले कदम" : "Next step"}</strong><ul className="list-disc pl-5 mt-2">{nextSteps.map((step) => <li key={step}>{step}</li>)}</ul></div>}</section>;
}

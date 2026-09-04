import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import {
  api,
  ApiError,
  EvidenceRecommendation,
  EvidenceStatus,
  NoticeCard,
  OFFICIAL_EFILING_PORTAL_URL,
  ScrutinyQuestion,
  ScrutinyRequestsResult,
  ScrutinyResolveResult,
  store,
  verifiedIncomeTaxUrl,
} from "../lib";
import {
  CitationChips,
  NoticeFactsCard,
  PrimaryButton,
  ScreenFrame,
  SecondaryButton,
  TaxTermExplanationCard,
  WhyDrawer,
  WorkflowLayout,
} from "../components";

type Stage = "requests" | "confirm" | "questions" | "result" | "draft" | "review" | "final" | "refusal";

const text = (value: Record<string, string> | undefined, locale: string) =>
  value?.[locale] ?? value?.en ?? "";

const statusLabel = (status: string | undefined, locale: string) => ({
  not_started: locale === "hi" ? "शुरू नहीं हुआ" : "Not started",
  need_information: locale === "hi" ? "जानकारी चाहिए" : "Need info",
  documents_needed: locale === "hi" ? "दस्तावेज़ चाहिए" : "Docs needed",
  ready_for_response: locale === "hi" ? "उत्तर तैयार" : "Ready",
  reviewed: locale === "hi" ? "समीक्षा पूर्ण" : "Reviewed",
}[status || "not_started"]);

function ErrorState({ error, retry }: { error: ApiError | Error; retry: () => void }) {
  const { t } = useI18n();
  const message =
    error instanceof ApiError && error.status === 404
      ? t("scrutiny.error404")
      : error instanceof ApiError && error.status === 429
      ? t("scrutiny.error429")
      : error instanceof ApiError && error.status === 503
      ? t("scrutiny.error503")
      : t("scrutiny.errorGeneric");
  return (
    <div className="app-empty">
      <p className="app-section-label">ERROR</p>
      <p>{message}</p>
      <button className="app-primary mt-5" onClick={retry}>
        {t("scrutiny.retry")}
      </button>
    </div>
  );
}

export default function Scrutiny() {
  const { id = "" } = useParams();
  const { locale, t } = useI18n();
  const restored = store.scrutinyStage(id) as Stage;
  const isUploaded = store.uploadedNoticeId() === id;
  const [stage, setStageState] = useState<Stage>(
    restored === "questions" && !store.extractionConfirmed(id) ? "requests" : restored || "requests"
  );
  const [requestIndex, setRequestIndex] = useState(0);
  const [viewAllRequests, setViewAllRequests] = useState(false);
  const [notice, setNotice] = useState<NoticeCard | null>(null);
  const [data, setData] = useState<ScrutinyRequestsResult | null>(null);
  const [questions, setQuestions] = useState<ScrutinyQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>(() => store.answers(id));
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<ScrutinyResolveResult | null>(null);
  const [draft, setDraft] = useState(() => store.draft(id) ?? "");
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [finalCopied, setFinalCopied] = useState(false);
  const [checklistState, setChecklistState] = useState<Record<string, boolean>>({});
  const [evidence, setEvidence] = useState<EvidenceRecommendation[]>([]);
  const [approval, setApproval] = useState(false);

  const setStage = (next: Stage) => {
    setStageState(next);
    store.setScrutinyStage(id, next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleChecklistToggle = (key: string) => {
    setChecklistState((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const downloadDraft = () => {
    const blob = new Blob([draft], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tax-mitra-response-${id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAsMarkdown = () => {
    if (!draft || !id) return;
    const md = `# Tax Mitra Response Draft

**Notice:** Section 142(1) · Inquiry before assessment
**Assessment Year:** ${notice?.assessment_year || "2024-25"}
**Reference DIN:** ${notice?.official_reference || "DEMO"}

---

${draft}
`;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tax-mitra-response-${id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAsPdf = () => {
    if (!draft || !id) return;
    const printContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Tax Mitra Response Draft</title>
  <style>
    body { font-family: 'Inter', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #101115; }
    h1 { border-bottom: 2px solid #101115; padding-bottom: 10px; font-size: 24px; }
    .meta { color: #555; margin-bottom: 30px; font-size: 14px; }
    .draft { white-space: pre-wrap; font-size: 15px; }
    .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #777; }
  </style>
</head>
<body>
  <h1>Tax Mitra Response Draft</h1>
  <div class="meta">
    <p><strong>Notice:</strong> Section 142(1) · ${notice?.title[locale] ?? notice?.title.en ?? "Inquiry before assessment"}</p>
    <p><strong>Assessment Year:</strong> ${notice?.assessment_year || "2024-25"}</p>
  </div>
  <div class="draft">${draft}</div>
  <div class="footer">
    <p>Generated by Tax Mitra for official submission on the Income Tax Department e-Filing portal.</p>
    <p>Tax Mitra does not submit on your behalf. Submit via e-Proceedings on incometax.gov.in.</p>
  </div>
</body>
</html>`;
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.print();
    }
  };

  const load = () => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    Promise.all([
      isUploaded ? Promise.resolve(null) : api.notice(id),
      api.scrutinyRequests(id, locale, true, controller.signal),
    ])
      .then(([n, r]) => {
        setNotice(n);
        setData(r);
        setLoading(false);
      })
      .catch((e) => {
        if (e.name !== "AbortError") {
          setError(e);
          setLoading(false);
        }
      });
    return () => controller.abort();
  };

  useEffect(load, [id, locale]);

  const confirm = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.scrutinyQuestions(id, locale, true);
      store.setExtractionConfirmed(id, true);
      setQuestions(response.questions);
      setIndex(Math.max(0, response.questions.findIndex((q) => !answers[q.id])));
      setStage("questions");
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  };

  const reject = async () => {
    setLoading(true);
    try {
      setResult(await api.resolveScrutiny(id, {}, false));
      setStage("refusal");
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  };

  const answer = async (value: string) => {
    const q = questions[index];
    const next = { ...answers, [q.id]: value };
    setAnswers(next);
    store.setAnswers(id, next);
    if (index < questions.length - 1) {
      setIndex(index + 1);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const resolved = await api.resolveScrutiny(
        id,
        next,
        true,
        undefined,
        Object.fromEntries(evidence.map((item) => [item.document_id, item.status]))
      );
      setResult(resolved);
      setEvidence(resolved.evidence ?? []);
      setDraft(store.draft(id) ?? resolved.draft ?? "");
      setStage("result");
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  };

  const ensureQuestions = async () => {
    if (!questions.length) {
      const r = await api.scrutinyQuestions(id, locale, true);
      setQuestions(r.questions);
    }
    setStage("questions");
  };

  const approveReview = async () => {
    if (!result) return;
    setLoading(true);
    setError(null);
    try {
      const outcome = await api.approveScrutiny(
        id,
        answers,
        draft,
        approval,
        Object.fromEntries(evidence.map((item) => [item.document_id, item.status]))
      );
      if (outcome.handoff_allowed) {
        setStage("final");
      } else {
        setError(new Error([outcome.message, ...(outcome.missing ?? [])].filter(Boolean).join(" ")));
      }
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  };

  const handleEvidenceStatusChange = async (documentId: string, status: EvidenceStatus) => {
    const next = evidence.map((item) =>
      item.document_id === documentId ? { ...item, status } : item
    );
    setEvidence(next);
    try {
      const projected = await api.evidence(
        id,
        Object.fromEntries(next.map((item) => [item.document_id, item.status]))
      );
      if (projected?.evidence) {
        setEvidence(projected.evidence);
      }
    } catch {
      // Keep optimistic state
    }
  };

  if (loading && !data) {
    return (
      <div className="workflow-shell">
        <div className="workflow-main">
          <div className="app-loading">{t("scrutiny.loading")}</div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="workflow-shell">
        <div className="workflow-main">
          <ErrorState error={error} retry={load} />
          {isUploaded ? (
            <Link to="/upload" className="app-primary mt-5">
              {t("scrutiny.newPdf")}
            </Link>
          ) : (
            <Link to="/notices" className="app-back-link mt-5">
              ← {t("j.back")}
            </Link>
          )}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const requests = data.requests ?? [];
  const q = questions[index];

  // Map stage to step index 0..5 for WorkflowLayout
  const stepIndex: 0 | 1 | 2 | 3 | 4 | 5 =
    stage === "requests" || stage === "confirm" || stage === "refusal"
      ? 0
      : stage === "questions"
      ? 1
      : stage === "result"
      ? 2
      : stage === "draft"
      ? 3
      : stage === "review"
      ? 4
      : 5;

  const activeNotice: NoticeCard = notice || {
    id,
    section: "142(1)",
    category: "scrutiny",
    supported: true,
    title: {
      en: "Inquiry before assessment under Section 142(1)",
      hi: "धारा 142(1) के तहत निर्धारण पूर्व जांच",
    },
    amount_in_question: 0,
    issue_date: "Not available in this notice",
    assessment_year: "2024-25",
    due_date: "Not available in this notice",
    days_remaining: null,
    status: "action_required",
    official_reference: "142(1) Scrutiny",
  };

  return (
    <WorkflowLayout currentStep={stepIndex} notice={activeNotice} noticeId={id}>
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 text-sm">
          {error.message}
        </div>
      )}

      {/* =========================================================================
          STEP 01: UNDERSTAND (Requests & Confirm)
         ========================================================================= */}
      {stage === "requests" && (
        <ScreenFrame
          whereAmI={
            locale === "hi"
              ? "चरण 01 / 06 · स्क्रूटनी नोटिस समझें"
              : "Step 01 of 06 · Understand Scrutiny Notice"
          }
          whatDoesThisMean={
            locale === "hi"
              ? `आपके नोटिस में ${requests.length} मदों की जानकारी मांगी गई है।`
              : `Your notice asks for ${requests.length} item${requests.length === 1 ? "" : "s"}.`
          }
          whatDoINeedToDo={
            locale === "hi"
              ? "विभाग द्वारा मांगी गई प्रत्येक मद की समीक्षा करें। विभाग की मूल शब्दावली नीचे सुरक्षित रखी गई है।"
              : "Review each item requested by the Department. The Department's original wording is preserved below."
          }
          primaryAction={
            viewAllRequests || requestIndex === requests.length - 1 ? (
              <PrimaryButton onClick={isUploaded ? ensureQuestions : () => setStage("confirm")}>
                {isUploaded ? t("scrutiny.checkRecords") : t("scrutiny.confirmList")} →
              </PrimaryButton>
            ) : (
              <PrimaryButton onClick={() => setRequestIndex(requestIndex + 1)}>
                {locale === "hi"
                  ? `अगला अनुरोध (${requestIndex + 2}/${requests.length}) →`
                  : `Next Request (${requestIndex + 2}/${requests.length}) →`}
              </PrimaryButton>
            )
          }
          secondaryAction={
            <Link to={isUploaded ? "/upload" : `/notices/${id}`} className="app-back-link">
              ← {t("j.back")}
            </Link>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: विभाग के हर अनुरोध के लिए सीधे स्पष्टीकरण प्रश्न।"
              : "Next step: Specific questions to identify the required facts and evidence for your response."
          }
        >
          <div className="space-y-6">
            {notice && <NoticeFactsCard notice={notice} />}

            <div className="p-4 bg-blue-50/60 border border-blue-200">
              <p className="text-sm font-bold text-slate-900">
                {locale === "hi" ? "स्क्रूटनी जांच (धारा 142(1))" : "Section 142(1) Scrutiny Inquiry"}
              </p>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                {locale === "hi"
                  ? "आयकर विभाग ने निर्धारण से पूर्व विशिष्ट जानकारी एवं खाते प्रस्तुत करने को कहा है। टैक्स मित्र ने आपके नोटिस से निम्नलिखित अनुरोध निकाले हैं:"
                  : "The Income Tax Department has called for production of accounts and specific explanations. Tax Mitra has extracted each departmental request below:"}
              </p>
            </div>

            {/* Stepper Control Bar */}
            {!viewAllRequests && requests.length > 1 && (
              <div className="request-stepper-bar">
                <div className="flex items-center gap-3">
                  <span className="stepper-progress-pill">
                    {locale === "hi"
                      ? `अनुरोध ${String(requestIndex + 1).padStart(2, "0")} / ${String(requests.length).padStart(2, "0")}`
                      : `REQUEST ${String(requestIndex + 1).padStart(2, "0")} OF ${String(requests.length).padStart(2, "0")}`}
                  </span>
                  <div className="request-jump-pills">
                    {requests.map((_, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => setRequestIndex(i)}
                        className={`request-jump-pill ${i === requestIndex ? "is-active" : ""}`}
                        title={`Go to request ${i + 1}`}
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setViewAllRequests(true)}
                  className="text-xs font-semibold text-blue-600 hover:underline"
                >
                  {locale === "hi" ? `सभी ${requests.length} अनुरोध एक साथ देखें` : `View all ${requests.length} requests at once`}
                </button>
              </div>
            )}

            {viewAllRequests && (
              <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  {locale === "hi" ? `सभी ${requests.length} अनुरोध दिखाए जा रहे हैं` : `Showing all ${requests.length} requests`}
                </span>
                <button
                  type="button"
                  onClick={() => setViewAllRequests(false)}
                  className="text-xs font-semibold text-blue-600 hover:underline"
                >
                  {locale === "hi" ? "एक-एक करके देखें (चरणबद्ध)" : "Focus on one request at a time"}
                </button>
              </div>
            )}

            {/* Scrutiny Request Cards */}
            <div className="space-y-4">
              {(viewAllRequests ? requests : requests.slice(requestIndex, requestIndex + 1)).map((r, i) => {
                const actualIndex = viewAllRequests ? i : requestIndex;
                return (
                  <div key={r.id} className="scrutiny-request-card">
                    <div className="scrutiny-request-header">
                      <span className="request-num-badge">{String(actualIndex + 1).padStart(2, "0")}</span>
                      <div className="request-header-content">
                        <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
                          {locale === "hi" ? "विभाग क्या मांग रहा है" : "What the Department is Asking"}
                        </p>
                        <blockquote className="request-original-quote">
                          "{r.original_text}"
                        </blockquote>
                        <TaxTermExplanationCard
                          termKey={r.response_section}
                          customTerm={r.response_section}
                          customPlain={text(r.plain_language_explanation, locale) || r.response_section}
                          citations={r.citations}
                        />
                      </div>
                    </div>

                    <div className="scrutiny-request-details">
                      <div className="request-detail-row">
                        <span className="detail-label">
                          {locale === "hi" ? "आवश्यक जानकारी" : "Information You Need to Provide"}
                        </span>
                        <p className="detail-text">
                          {r.why_required
                            ? text(r.why_required, locale)
                            : locale === "hi"
                            ? "लेन-देन का ब्योरा एवं संबंधित खाता बही में प्रविष्टियां।"
                            : "Clarification of transaction dates, amounts, and ledger reconciliation."}
                        </p>
                      </div>

                      {r.required_evidence.length > 0 && (
                        <div className="request-detail-row">
                          <span className="detail-label">
                            {locale === "hi" ? "मददगार दस्तावेज़" : "Documents That May Help"}
                          </span>
                          <ul className="list-disc pl-5 text-xs text-slate-700 space-y-1">
                            {r.required_evidence.map((e, j) => (
                              <li key={j}>{text(e, locale)}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-2 border-t border-slate-200 text-xs">
                        <span className="font-semibold text-slate-500">
                          {locale === "hi" ? "स्थिति:" : "Status:"}{" "}
                          <span className="text-slate-900 font-bold">
                            {statusLabel(r.workflow_status, locale)}
                          </span>
                        </span>

                        {r.citations.length > 0 && (
                          <div className="flex items-center gap-2">
                            <span className="text-slate-400">
                              {locale === "hi" ? "स्रोत:" : "Sources:"}
                            </span>
                            <CitationChips citations={r.citations} />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Stepper bottom navigation buttons when in focused view */}
            {!viewAllRequests && requests.length > 1 && (
              <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                <SecondaryButton
                  onClick={() => setRequestIndex(Math.max(0, requestIndex - 1))}
                  disabled={requestIndex === 0}
                >
                  ← {locale === "hi" ? "पिछला अनुरोध" : "Previous Request"}
                </SecondaryButton>
                {requestIndex < requests.length - 1 ? (
                  <PrimaryButton onClick={() => setRequestIndex(requestIndex + 1)}>
                    {locale === "hi"
                      ? `अगला अनुरोध (${requestIndex + 2}/${requests.length}) →`
                      : `Next Request (${requestIndex + 2}/${requests.length}) →`}
                  </PrimaryButton>
                ) : (
                  <PrimaryButton onClick={isUploaded ? ensureQuestions : () => setStage("confirm")}>
                    {locale === "hi"
                      ? `सभी ${requests.length} अनुरोधों की समीक्षा पूर्ण · प्रश्नों पर आगे बढ़ें →`
                      : `All ${requests.length} Requests Reviewed · Continue to Questions →`}
                  </PrimaryButton>
                )}
              </div>
            )}

            {isUploaded && (
              <div className="p-4 bg-slate-50 border border-slate-200 text-xs text-slate-600">
                <strong>{t("scrutiny.confirmedExtraction")}:</strong> {t("scrutiny.confirmedText")}
              </div>
            )}
          </div>
        </ScreenFrame>
      )}

      {/* Confirmation Checkpoint */}
      {stage === "confirm" && (
        <ScreenFrame
          whereAmI={
            locale === "hi" ? "सत्यापन · अनुरोध पुष्टि" : "Checkpoint · Confirm Extraction"
          }
          whatDoesThisMean={t("scrutiny.confirmTitle")}
          whatDoINeedToDo={t("scrutiny.confirmSub", { count: String(requests.length) })}
          primaryAction={
            <PrimaryButton onClick={confirm}>{t("scrutiny.yesCorrect")} →</PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={reject} className="!border-red-300 !text-red-700 hover:!bg-red-50">
              {t("scrutiny.somethingWrong")}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: विभाग के प्रश्नों का उत्तर देकर आवश्यक दस्तावेज़ और प्रारूप तय करें।"
              : "Next step: Answer dynamic questions for each departmental request."
          }
        >
          <div className="p-4 bg-slate-50 border border-slate-200">
            <p className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-2">
              {locale === "hi" ? "पहचाने गए अनुरोध" : "Extracted Request Summary"}
            </p>
            <ol className="list-decimal pl-5 text-sm text-slate-800 space-y-2">
              {requests.map((r, i) => (
                <li key={i}>
                  <strong>{text(r.plain_language_explanation, locale) || r.response_section}</strong>
                  <p className="text-xs text-slate-500 italic mt-0.5">"{r.original_text}"</p>
                </li>
              ))}
            </ol>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 02: QUESTIONS
         ========================================================================= */}
      {stage === "questions" && q && (
        <ScreenFrame
          whereAmI={
            locale === "hi"
              ? `चरण 02 / 06 · प्रश्न ${index + 1} / ${questions.length}`
              : `Step 02 of 06 · Question ${index + 1} of ${questions.length}`
          }
          whatDoesThisMean={q.text}
          whatDoINeedToDo={
            q.help ||
            (locale === "hi"
              ? "अपने बैंक विवरण या बहीखातों के आधार पर उपयुक्त विकल्प चुनें।"
              : "Select the option that matches your actual financial records and books of account.")
          }
          primaryAction={null}
          secondaryAction={
            <SecondaryButton onClick={() => (index > 0 ? setIndex(index - 1) : setStage("requests"))}>
              ← {locale === "hi" ? "पिछला प्रश्न" : "Previous Question"}
            </SecondaryButton>
          }
          whatHappensNext={
            index < questions.length - 1
              ? locale === "hi"
                ? `अगला कदम: प्रश्न ${index + 2} / ${questions.length}`
                : `Next step: Question ${index + 2} of ${questions.length}`
              : locale === "hi"
              ? "अगला कदम: आपके उत्तरों के आधार पर आवश्यक दस्तावेज़ों की सूची।"
              : "Next step: Evidence & document checklist tailored to your responses."
          }
        >
          <div className="space-y-6">
            {q.help && (
              <div className="upfront-why-banner">
                <span className="upfront-why-title">
                  {locale === "hi" ? "यह प्रश्न क्यों पूछा जा रहा है?" : "WHY ARE WE ASKING THIS?"}
                </span>
                <p className="upfront-why-text">{q.help}</p>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {q.options.map((o) => {
                const isSelected = answers[q.id] === o.id;
                return (
                  <button
                    key={o.id}
                    onClick={() => answer(o.id)}
                    className={`p-4 text-center border font-semibold text-base transition-all min-h-[56px] flex items-center justify-center ${
                      isSelected
                        ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                        : "bg-white text-slate-900 border-slate-300 hover:border-slate-900"
                    }`}
                  >
                    {o.label}
                  </button>
                );
              })}
            </div>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 03: DOCUMENTS
         ========================================================================= */}
      {stage === "result" && result && (
        <ScreenFrame
          whereAmI={
            locale === "hi"
              ? "चरण 03 / 06 · दस्तावेज़ तैयारी"
              : "Step 03 of 06 · Documents & Evidence"
          }
          whatDoesThisMean={
            text(result.path?.headline, locale) ||
            (locale === "hi"
              ? "हर अनुरोध के लिए संभावित प्रमाण"
              : "Supporting Evidence for Section 142(1)")
          }
          whatDoINeedToDo={
            locale === "hi"
              ? "प्रत्येक दस्तावेज़ की उपलब्धता स्थिति चुनें। 'पक्का नहीं' रहने पर अंतिम समीक्षा में ध्यान दिलाया जाएगा।"
              : "Mark whether you have each document or need to find it. Items marked 'Not sure' will remain flagged for review."
          }
          primaryAction={
            <PrimaryButton onClick={() => setStage("draft")}>
              {locale === "hi" ? "उत्तर का प्रारूप देखें" : "Prepare Response Draft"} →
            </PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={ensureQuestions}>
              ← {locale === "hi" ? "उत्तर बदलें" : "Change Answers"}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: आपके उत्तरों एवं उपलब्ध प्रमाणों के आधार पर औपचारिक उत्तर का प्रारूप।"
              : "Next step: Formal clause-by-clause response draft grounded in tax provisions."
          }
        >
          <div className="space-y-6">
            {result.path?.professional_help_recommended && (
              <div className="p-4 bg-amber-50 border border-amber-200">
                <p className="text-xs font-bold uppercase tracking-wider text-amber-900 mb-1">
                  {locale === "hi" ? "पेशेवर समीक्षा अनुशंसित" : "Professional Review Recommended"}
                </p>
                <p className="text-sm text-amber-950">
                  {t("scrutiny.professionalText")}
                </p>
              </div>
            )}

            {/* Evidence items list */}
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                {locale === "hi" ? "दस्तावेज़ उपलब्धता चेकलिस्ट" : "Evidence Availability Checklist"}
              </p>

              {evidence.length > 0 ? (
                <div className="space-y-3">
                  {evidence.map((item) => (
                    <div key={item.document_id} className="evidence-item-card">
                      <div className="evidence-header">
                        <div>
                          <p className="evidence-name">{text(item.document_name, locale)}</p>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {item.requirement_level === "required"
                              ? locale === "hi"
                                ? "नोटिस में सीधे मांगा गया"
                                : "Directly requested in notice"
                              : locale === "hi"
                              ? "संभावित रूप से उपयोगी प्रमाण"
                              : "Supporting evidence"}
                          </p>
                        </div>
                        <span
                          className={`evidence-status-pill ${
                            item.status === "have"
                              ? "bg-emerald-100 text-emerald-800"
                              : item.status === "need_to_find"
                              ? "bg-amber-100 text-amber-800"
                              : item.status === "dont_have"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {item.status === "have"
                            ? locale === "hi"
                              ? "उपलब्ध"
                              : "Have it"
                            : item.status === "need_to_find"
                            ? locale === "hi"
                              ? "ढूंढना है"
                              : "Need to find"
                            : item.status === "dont_have"
                            ? locale === "hi"
                              ? "नहीं है"
                              : "Don't have"
                            : locale === "hi"
                            ? "पक्का नहीं"
                            : "Not sure"}
                        </span>
                      </div>

                      <p className="evidence-reason">{text(item.reason, locale)}</p>

                      <div className="evidence-status-actions-row">
                        <button
                          type="button"
                          onClick={() => handleEvidenceStatusChange(item.document_id, "have")}
                          className={`status-choice-btn ${item.status === "have" ? "is-have" : ""}`}
                        >
                          ✓ {locale === "hi" ? "मेरे पास है" : "Have it"}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleEvidenceStatusChange(item.document_id, "need_to_find")}
                          className={`status-choice-btn ${item.status === "need_to_find" ? "is-need-find" : ""}`}
                        >
                          ⚲ {locale === "hi" ? "ढूंढना है" : "Need to find it"}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleEvidenceStatusChange(item.document_id, "dont_have")}
                          className={`status-choice-btn ${item.status === "dont_have" ? "is-dont-have" : ""}`}
                        >
                          ✕ {locale === "hi" ? "नहीं है" : "Don't have it"}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleEvidenceStatusChange(item.document_id, "not_sure")}
                          className={`status-choice-btn ${item.status === "not_sure" ? "is-not-sure" : ""}`}
                        >
                          ? {locale === "hi" ? "पक्का नहीं" : "Not sure"}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 bg-slate-50 border border-slate-200 text-sm text-slate-600">
                  {locale === "hi"
                    ? "इस निर्धारण वर्ष के लिए कोई अतिरिक्त दस्तावेज़ आवश्यक नहीं हैं।"
                    : "Standard ledger extracts and return acknowledgment are sufficient for this notice."}
                </div>
              )}
            </div>

            <WhyDrawer
              title={
                locale === "hi"
                  ? "दस्तावेज़ स्थिति क्यों महत्वपूर्ण है?"
                  : "Why is document availability tracking important?"
              }
            >
              <p className="text-sm text-slate-700 leading-relaxed">
                {locale === "hi"
                  ? "धारा 142(1) के तहत विभाग को मांगे गए दस्तावेज समय पर न देने पर धारा 144 (बेस्ट जजमेंट असेसमेंट) की कार्रवाई हो सकती है। टैक्स मित्र कोई भी फाइल अपलोड या स्टोर नहीं करता, लेकिन आपकी तत्परता सुनिश्चित करता है।"
                  : "Under Section 142(1), failure to produce accounts or documents can lead to best judgment assessment under Section 144. Tax Mitra does not store or upload your files, but helps ensure you submit a complete evidence package on the official portal."}
              </p>
            </WhyDrawer>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 04: RESPONSE (Guided Draft Editor)
         ========================================================================= */}
      {stage === "draft" && (
        <ScreenFrame
          whereAmI={
            locale === "hi"
              ? "चरण 04 / 06 · उत्तर का प्रारूप"
              : "Step 04 of 06 · Official Response Draft"
          }
          whatDoesThisMean={
            locale === "hi"
              ? "धारा 142(1) के लिए औपचारिक उत्तर प्रारूप"
              : "Clause-by-Clause Response Draft"
          }
          whatDoINeedToDo={
            locale === "hi"
              ? "प्रारूप की समीक्षा करें। आप सीधे नीचे संपादक में कोई भी सुधार या विवरण जोड़ सकते हैं।"
              : "Review the drafted response below. You can edit directly to adjust specific dates or ledger figures."
          }
          primaryAction={
            <PrimaryButton
              onClick={() => {
                store.setDraft(id, draft);
                setStage("review");
              }}
            >
              {t("j.acceptDraft")} →
            </PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={() => setStage("result")}>
              ← {locale === "hi" ? "दस्तावेज़ों पर वापस जाएं" : "Back to Documents"}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: अंतिम समीक्षा, सांविधिक जांच और स्पष्ट अनुमोदन।"
              : "Next step: Executive review, statutory checks, and explicit taxpayer approval."
          }
        >
          <div className="space-y-6">
            {/* Guided Context Box */}
            <div className="p-4 bg-slate-50 border border-slate-200">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                {locale === "hi" ? "आपके उत्तरों के आधार पर" : "Based On Your Confirmed Answers"}
              </p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(answers).map(([qid, val]) => (
                  <span
                    key={qid}
                    className="inline-block px-2.5 py-1 bg-white border border-slate-300 text-xs font-medium text-slate-800"
                  >
                    Q: {qid} → <strong>{val}</strong>
                  </span>
                ))}
              </div>
              <p className="text-xs text-slate-600 mt-2">
                {locale === "hi"
                  ? "टैक्स मित्र ने आपके द्वारा पुष्टि की गई जानकारी के आधार पर यह उत्तर तैयार किया है। आगे बढ़ने से पहले इसकी समीक्षा करें।"
                  : "Tax Mitra prepared this response based on the information you confirmed. Review it before continuing."}
              </p>
            </div>

            {/* Editable Draft Textarea */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                  {locale === "hi" ? "संपादन योग्य उत्तर प्रारूप" : "Editable Response Text"}
                </span>
                <span className="text-xs text-slate-500">
                  {draft.length} {locale === "hi" ? "अक्षर" : "characters"}
                </span>
              </div>
              <textarea
                className="w-full font-mono text-sm leading-relaxed p-4 border border-slate-300 focus:border-blue-600 focus:outline-none min-h-[360px] bg-white text-slate-900"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onBlur={() => store.setDraft(id, draft)}
                rows={16}
              />
            </div>

            {/* Draft Actions */}
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={async () => {
                  await navigator.clipboard.writeText(draft);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="px-4 py-2 text-xs font-bold border border-slate-300 bg-white hover:border-slate-900 text-slate-800 transition-colors"
              >
                {copied ? t("scrutiny.copied") : t("scrutiny.copyDraft")}
              </button>
              <button
                type="button"
                onClick={downloadDraft}
                className="px-4 py-2 text-xs font-bold border border-slate-300 bg-white hover:border-slate-900 text-slate-800 transition-colors"
              >
                {t("scrutiny.downloadDraft")}
              </button>
            </div>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 05: REVIEW (Executive Review & Approval Gate)
         ========================================================================= */}
      {stage === "review" && result && (
        <ScreenFrame
          whereAmI={
            locale === "hi"
              ? "चरण 05 / 06 · अंतिम समीक्षा एवं अनुमोदन"
              : "Step 05 of 06 · Executive Review & Approval"
          }
          whatDoesThisMean={t("j.reviewTitle")}
          whatDoINeedToDo={
            locale === "hi"
              ? "अपने उत्तर की सभी मदों की पुष्टि करें और आधिकारिक पोर्टल पर जाने के लिए अपनी स्पष्ट सहमति दें।"
              : "Verify the 5 readiness items below and give your explicit approval before accessing the e-Filing portal instructions."
          }
          primaryAction={
            <PrimaryButton disabled={!approval} onClick={approveReview}>
              {t("scrutiny.continueHandoff")} →
            </PrimaryButton>
          }
          secondaryAction={
            <SecondaryButton onClick={() => setStage("draft")}>
              ← {locale === "hi" ? "प्रारूप संपादित करें" : "Edit Response Draft"}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "अगला कदम: ई-फाइलिंग पोर्टल पर उत्तर दाखिल करने की चरणबद्ध गाइड।"
              : "Next step: Step-by-step submission instructions on the official Income Tax portal."
          }
        >
          <div className="space-y-6">
            {/* Executive Review Card */}
            <div className="executive-review-card">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">
                {locale === "hi" ? "कार्यकारी समीक्षा चेकलिस्ट" : "Executive Readiness Checklist"}
              </p>

              <div className="review-items-list">
                <div className="review-checklist-item">
                  <span className="review-item-name">
                    {locale === "hi" ? "नोटिस एवं धारा" : "Notice & Section"}
                  </span>
                  <span className="review-item-status">
                    Section 142(1) · AY {notice?.assessment_year || "2024-25"} ✓
                  </span>
                </div>

                <div className="review-checklist-item">
                  <span className="review-item-name">
                    {locale === "hi" ? "स्पष्टीकरण प्रश्न" : "Clarification Questions"}
                  </span>
                  <span className="review-item-status">
                    {Object.keys(answers).length} {locale === "hi" ? "उत्तर दिए गए" : "completed"} ✓
                  </span>
                </div>

                <div className="review-checklist-item">
                  <span className="review-item-name">
                    {locale === "hi" ? "दस्तावेज़ उपलब्धता" : "Document Readiness"}
                  </span>
                  <span className="review-item-status">
                    {evidence.filter((e) => e.status === "have").length} / {evidence.length || requests.length}{" "}
                    {locale === "hi" ? "उपलब्ध" : "marked ready"}
                  </span>
                </div>

                <div className="review-checklist-item">
                  <span className="review-item-name">
                    {locale === "hi" ? "उत्तर का प्रारूप" : "Draft Response"}
                  </span>
                  <span className="review-item-status">
                    {draft.length > 0 ? (locale === "hi" ? "तैयार ✓" : "Ready ✓") : "Incomplete"}
                  </span>
                </div>

                <div className="review-checklist-item">
                  <span className="review-item-name">
                    {locale === "hi" ? "सांविधिक आधार" : "Statutory Grounding"}
                  </span>
                  <span className="review-item-status">
                    {locale === "hi" ? "आयकर अधिनियम, 1961 सत्यापित ✓" : "Verified against Act ✓"}
                  </span>
                </div>
              </div>

              {/* Deadline reminder */}
              <div className="p-3 bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center justify-between">
                <span>{locale === "hi" ? "प्रतिक्रिया की अंतिम तिथि:" : "Response Deadline:"}</span>
                <strong className="text-slate-900 font-bold">
                  {result.deadline?.due_date ?? notice?.due_date ?? "Not available in this notice"}
                </strong>
              </div>
            </div>

            {/* Safety checks */}
            {result.safety_review && (
              <div className="p-4 bg-slate-50 border border-slate-200">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  {locale === "hi" ? "सुरक्षा जांच" : "Safety System Checks"}
                </p>
                <div className="space-y-2">
                  {result.safety_review.checks.map((check) => (
                    <div key={check.key} className="flex items-start gap-2 text-xs">
                      <span className={check.status === "passed" ? "text-emerald-700 font-bold" : "text-amber-700 font-bold"}>
                        {check.status === "passed" ? "✓" : "!"}
                      </span>
                      <span className="text-slate-800 font-medium">
                        {check.label}
                        {check.missing && <span className="text-slate-500 block">{check.missing}</span>}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Explicit Human Approval Gate */}
            <div className="approval-gate-box">
              <label className="approval-gate-label">
                <input
                  type="checkbox"
                  checked={approval}
                  onChange={(e) => setApproval(e.target.checked)}
                />
                <span>
                  {locale === "hi"
                    ? "मैंने response draft, documents और sources की समीक्षा की है और official portal पर स्वयं review करने की मंजूरी देता/देती हूं।"
                    : "I have reviewed the response draft, documents, and sources, and approve moving to the official portal for my own review."}
                </span>
              </label>
            </div>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          STEP 06: ACT (Official Portal Guide)
         ========================================================================= */}
      {stage === "final" && (
        <ScreenFrame
          whereAmI={
            locale === "hi"
              ? "चरण 06 / 06 · ई-फाइलिंग पोर्टल पर कार्रवाई"
              : "Step 06 of 06 · Submit on Official Portal"
          }
          whatDoesThisMean={t("j.finalTitle")}
          whatDoINeedToDo={
            locale === "hi"
              ? "नीचे दिए गए 7 चरणों का पालन करें। ड्राफ्ट डाउनलोड करें और आधिकारिक आयकर ई-फाइलिंग पोर्टल पर ई-प्रोसीडिंग्स में जमा करें।"
              : "Follow the 7 official submission steps below to submit your response under e-Proceedings on incometax.gov.in."
          }
          primaryAction={
            <a
              className="app-primary-btn"
              href={OFFICIAL_EFILING_PORTAL_URL}
              target="_blank"
              rel="noopener noreferrer"
            >
              {t("j.continuePortal")} ↗
            </a>
          }
          secondaryAction={
            <SecondaryButton onClick={() => setStage("review")}>
              ← {t("j.back")}
            </SecondaryButton>
          }
          whatHappensNext={
            locale === "hi"
              ? "जमा करने के बाद पावती (Acknowledgment Receipt) और DIN सुरक्षित रखें।"
              : "Keep the submission acknowledgment receipt and DIN safe for your records."
          }
        >
          <div className="space-y-6">
            {/* Download and Copy Box */}
            <div className="p-4 bg-slate-50 border border-slate-200">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                {t("j.downloadDraft")}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={downloadDraft}
                  className="px-4 py-2.5 text-xs font-bold border border-slate-300 bg-white hover:border-slate-900 text-slate-800 transition-colors text-center"
                >
                  {t("j.downloadTxt")}
                </button>
                <button
                  type="button"
                  onClick={downloadAsMarkdown}
                  className="px-4 py-2.5 text-xs font-bold border border-slate-300 bg-white hover:border-slate-900 text-slate-800 transition-colors text-center"
                >
                  {t("j.downloadMd")}
                </button>
                <button
                  type="button"
                  onClick={downloadAsPdf}
                  className="px-4 py-2.5 text-xs font-bold border border-slate-300 bg-white hover:border-slate-900 text-slate-800 transition-colors text-center"
                >
                  {t("j.downloadPdf")}
                </button>
              </div>
              <button
                type="button"
                onClick={async () => {
                  await navigator.clipboard.writeText(draft);
                  setFinalCopied(true);
                  setTimeout(() => setFinalCopied(false), 2000);
                }}
                className="text-xs text-blue-600 hover:underline mt-3 block font-semibold"
              >
                {finalCopied ? t("scrutiny.copied") : t("scrutiny.copyDraft")}
              </button>
            </div>

            {/* Official Submission Timeline */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                {t("j.actionPlan")}
              </p>

              <div className="action-timeline">
                <div className="action-step">
                  <span className="action-number">01</span>
                  <div>
                    <h3>{t("j.act01")}</h3>
                    <p>{t("j.act01Desc")}</p>
                  </div>
                </div>

                <div className="action-step">
                  <span className="action-number">02</span>
                  <div>
                    <h3>{t("j.act02")}</h3>
                    <p>{t("j.act02Desc")}</p>
                  </div>
                </div>

                <div className="action-step">
                  <span className="action-number">03</span>
                  <div>
                    <h3>{t("j.act03")}</h3>
                    <p>{t("j.act03Desc")}</p>
                  </div>
                </div>

                <div className="action-step">
                  <span className="action-number">04</span>
                  <div>
                    <h3>{t("j.act04")}</h3>
                    <p className="font-mono text-xs text-slate-600">{t("j.portalNav")}</p>
                  </div>
                </div>

                <div className="action-step">
                  <span className="action-number">05</span>
                  <div>
                    <h3>{t("j.act05")}</h3>
                    <p>{t("j.act05Desc142")}</p>
                  </div>
                </div>

                <div className="action-step">
                  <span className="action-number">06</span>
                  <div>
                    <h3>{t("j.act06")}</h3>
                    <p>{t("j.act06Desc")}</p>
                  </div>
                </div>

                <div className="action-step">
                  <span className="action-number">07</span>
                  <div>
                    <h3>{t("j.act07")}</h3>
                    <p>{t("j.act07Desc")}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Pre-submission Checklist */}
            <div className="p-4 bg-slate-50 border border-slate-200">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                {t("j.beforeSubmit")}
              </p>
              <div className="space-y-2">
                {[
                  { key: "c1", label: t("j.check01") },
                  { key: "c2", label: t("j.check02") },
                  { key: "c3", label: t("j.check03") },
                  { key: "c4", label: t("j.check04") },
                  { key: "c5", label: t("j.check05") },
                ].map((item) => (
                  <label key={item.key} className="flex items-center gap-2.5 text-xs text-slate-800 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checklistState[item.key] || false}
                      onChange={() => handleChecklistToggle(item.key)}
                      className="w-4 h-4 accent-blue-600"
                    />
                    <span>{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Safety Boundary */}
            <div className="p-4 bg-blue-50 border border-blue-200 text-xs text-slate-700 space-y-1">
              <p className="font-bold text-slate-900">{t("j.finalBoundary")}</p>
              <p>{t("j.finalInstruction")}</p>
            </div>
          </div>
        </ScreenFrame>
      )}

      {/* =========================================================================
          REFUSAL / SAFE STOP STATE
         ========================================================================= */}
      {stage === "refusal" && result && (
        <ScreenFrame
          whereAmI={locale === "hi" ? "सुरक्षित विराम" : "Safe Stop"}
          whatDoesThisMean={text(result.headline, locale) || t("scrutiny.safeStop")}
          whatDoINeedToDo={
            text(result.why, locale) ||
            "The system identified high extraction uncertainty or non-standard provisions."
          }
          primaryAction={
            <PrimaryButton onClick={() => setStage("requests")}>
              ← {t("scrutiny.reviewAgain")}
            </PrimaryButton>
          }
          secondaryAction={null}
          whatHappensNext="Consult a Chartered Accountant or review your notice directly on incometax.gov.in."
        >
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 border border-slate-200">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                {t("scrutiny.refusalSuggestion")}
              </p>
              <p className="text-sm text-slate-800">{text(result.suggestion, locale)}</p>
            </div>

            {result.official_links && result.official_links.length > 0 && (
              <div className="p-4 bg-white border border-slate-200 space-y-2">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  {locale === "hi" ? "आधिकारिक स्रोत" : "Official Resources"}
                </p>
                {result.official_links.map((link, idx) => (
                  <a
                    key={idx}
                    className="block text-xs font-semibold text-blue-600 hover:underline"
                    href={verifiedIncomeTaxUrl(link.url)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {text(link.label, locale)} ↗
                  </a>
                ))}
              </div>
            )}
          </div>
        </ScreenFrame>
      )}
    </WorkflowLayout>
  );
}

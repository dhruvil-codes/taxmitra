import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import {
  api,
  EvidenceRecommendation,
  NoticeCard,
  Question,
  QuestionAnswer,
  ScrutinyRequest,
  UniversalWorkflowContract,
  WorkflowCapability,
  verifiedIncomeTaxUrl,
  OFFICIAL_EFILING_PORTAL_URL,
  store,
} from "../lib";
import {
  CapabilityBadge,
  CapabilityBoundary,
  ContractEvidence,
  ContractExplanation,
  ContractQuestion,
  ContractRequests,
} from "../components/UniversalWorkflow";
import { NoticeFactsCard, PrimaryButton, ScreenFrame, WorkflowLayout } from "../components";

type Phase = "understand" | "requests" | "questions" | "documents" | "response" | "review" | "act";

function userCapability(value: string | undefined): WorkflowCapability {
  return value === "SUPPORTED" || value === "PARTIAL_SUPPORT" || value === "EXPLANATION_ONLY" || value === "SAFE_STOP"
    ? value
    : "SAFE_STOP";
}

function questionText(question: Question): string {
  return question.text || "Please review this question.";
}

function normalizeQuestion(
  question: Question & { question_id?: string; question?: string; why_we_are_asking?: string; type?: Question["question_type"] }
): Question {
  return {
    id: question.id || question.question_id || "",
    text: question.text || question.question || "",
    help: question.help || question.why_we_are_asking || "",
    options: question.options || [],
    question_type: question.question_type || question.type,
    required: question.required,
    conditions: question.conditions,
    related_request_ids: question.related_request_ids,
  };
}

function questionIsVisible(question: Question, answers: Record<string, QuestionAnswer>): boolean {
  return (question.conditions ?? []).every((condition) => {
    const dependency = condition.depends_on ?? condition.question_id;
    const expected = condition.equals ?? condition.value;
    const answer = dependency ? answers[dependency] : undefined;
    const allowed = condition.one_of ?? condition.values;
    return !dependency || (Array.isArray(allowed) ? allowed.includes(String(answer)) : expected === undefined || (typeof answer === "string" && answer === expected));
  });
}

function ResponseDownloadToolbar({
  draft,
  notice,
  locale,
}: {
  draft: string;
  notice?: NoticeCard;
  locale: string;
}) {
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  const section = notice?.section || "Notice";
  const ay = notice?.assessment_year || "AY";
  const baseName = `Income_Tax_Reply_${section.replace(/[^a-zA-Z0-9_-]/g, "_")}_${ay}`;

  const handleDownloadTxt = () => {
    const blob = new Blob([draft], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${baseName}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadMd = () => {
    const blob = new Blob([draft], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${baseName}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = async () => {
    if (downloading) return;
    setDownloading(true);
    try {
      const blob = await api.exportResponse(draft, "pdf", baseName);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${baseName}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      window.print();
    } finally {
      setDownloading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // fallback
    }
  };

  return (
    <div className="response-download-toolbar" aria-label="Download response letter">
      <div className="download-toolbar-info">
        <span className="download-toolbar-label">
          {locale === "hi" ? "उत्तर डाउनलोड करें:" : "Download Response Letter:"}
        </span>
      </div>
      <div className="download-toolbar-buttons">
        <button
          type="button"
          onClick={handleDownloadPdf}
          disabled={downloading}
          className="download-btn download-btn--pdf"
          title="Download formatted A4 PDF letter"
        >
          <span className="btn-icon">📄</span>
          <span>{downloading ? (locale === "hi" ? "तैयार हो रहा है..." : "Generating PDF...") : "Download PDF (.pdf)"}</span>
        </button>
        <button
          type="button"
          onClick={handleDownloadTxt}
          className="download-btn download-btn--txt"
          title="Download as plain text file"
        >
          <span className="btn-icon">📝</span>
          <span>Download Text (.txt)</span>
        </button>
        <button
          type="button"
          onClick={handleDownloadMd}
          className="download-btn download-btn--md"
          title="Download as Markdown file"
        >
          <span className="btn-icon">⬇</span>
          <span>Download Markdown (.md)</span>
        </button>
        <button
          type="button"
          onClick={handleCopy}
          className="download-btn download-btn--copy"
          title="Copy response letter to clipboard"
        >
          <span className="btn-icon">{copied ? "✓" : "📋"}</span>
          <span>{copied ? (locale === "hi" ? "कॉपी हो गया!" : "Copied to clipboard!") : (locale === "hi" ? "कॉपी करें" : "Copy Draft")}</span>
        </button>
      </div>
    </div>
  );
}

export default function Journey() {
  const { id = "" } = useParams();
  const { locale } = useI18n();
  const [contract, setContract] = useState<UniversalWorkflowContract | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [requests, setRequests] = useState<ScrutinyRequest[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRecommendation[]>([]);
  const [mappedEvidence, setMappedEvidence] = useState<EvidenceRecommendation[]>([]);
  const [answers, setAnswers] = useState<Record<string, QuestionAnswer>>(() => (id ? (store.answers(id) as Record<string, QuestionAnswer>) : {}));
  const [questionIndex, setQuestionIndex] = useState(0);
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const startAtQuestions = Boolean(
    (location.state as { uploaded?: boolean; startStep?: string } | null)?.uploaded ||
    (location.state as { uploaded?: boolean; startStep?: string } | null)?.startStep === "questions" ||
    searchParams.get("step") === "questions"
  );
  const [phase, setPhase] = useState<Phase>("understand");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [editableDraft, setEditableDraft] = useState("");
  const [reviewApproved, setReviewApproved] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([api.notice(id), api.noticeWorkflow(id)])
      .then(async ([notice, routed]) => {
        const capability = userCapability(routed.workflow?.capability ?? routed.classification.capability);
        const backend = routed.contract;
        const base: UniversalWorkflowContract = {
          workflowId: routed.classification.workflow_id,
          category: routed.classification.category,
          title: routed.workflow?.title ?? notice.title,
          capability,
          confidence: routed.classification.confidence,
          groundingStatus: routed.classification.grounding_status,
          reason: routed.classification.reason,
          notice,
          requests: backend?.requests ?? [],
          questions: (backend?.questions ?? []).map(normalizeQuestion),
          evidence: backend?.evidence ?? [],
          action: backend?.action,
          nextSteps: backend?.next_steps ?? [
            "Review the original communication and its deadline.",
            "Use the official Income Tax e-Filing portal for any required action.",
          ],
          officialPortalUrl: verifiedIncomeTaxUrl(backend?.official_portal.url ?? OFFICIAL_EFILING_PORTAL_URL),
        };
        setContract(base);
        let loadedQuestions: Question[] = [];
        if (routed.contract) {
          setRequests(routed.contract.requests ?? []);
          setEvidence(routed.contract.evidence ?? []);
          loadedQuestions = (routed.contract.questions ?? []).map(normalizeQuestion);
          setQuestions(loadedQuestions);
        }
        if (capability === "SAFE_STOP" || capability === "EXPLANATION_ONLY") return;
        if (!loadedQuestions.length && !routed.contract?.requests?.length) {
          const workflowData = await api.workflowData(id, locale, base.workflowId);
          setRequests(workflowData.requests);
          setEvidence(workflowData.evidence);
          loadedQuestions = workflowData.questions;
          setQuestions(loadedQuestions);
        }
        if (startAtQuestions && loadedQuestions.length > 0) {
          setPhase("questions");
        }
      })
      .catch(() => setError("We could not load this workflow contract."));
  }, [id, locale, startAtQuestions]);

  // Persist answers so navigation back and forth never loses them
  useEffect(() => {
    if (id && Object.keys(answers).length > 0) {
      store.setAnswers(id, answers as Record<string, string>);
    }
  }, [id, answers]);

  // Sync editable draft whenever the resolved draft changes
  useEffect(() => {
    const draft = typeof result?.draft === "string" ? result.draft : "";
    if (draft) setEditableDraft(draft);
  }, [result]);

  const visibleQuestions = questions.filter((question) => questionIsVisible(question, answers));
  const visibleQuestion = visibleQuestions[questionIndex];
  const hasQuestions = visibleQuestions.length > 0;
  const capability = contract?.capability ?? "SAFE_STOP";
  const title = contract?.title[locale] ?? contract?.title.en ?? "Income Tax communication";

  const resolveWorkflow = async (currentAnswers: Record<string, QuestionAnswer>) => {
    if (!contract || resolving) return null;
    setResolving(true);
    try {
      const response = await api.resolveWorkflow(id, contract.workflowId, currentAnswers);
      const res = response as unknown as Record<string, unknown>;
      setResult(res);
      if (res?.evidence && Array.isArray(res.evidence)) {
        setMappedEvidence(res.evidence as EvidenceRecommendation[]);
      }
      return res;
    } catch {
      setError("We could not resolve this workflow safely.");
      return null;
    } finally {
      setResolving(false);
    }
  };

  const handleQuestionContinue = async () => {
    if (!visibleQuestion) return;
    if (questionIndex + 1 < visibleQuestions.length) {
      setQuestionIndex(questionIndex + 1);
    } else {
      const res = await resolveWorkflow(answers);
      if (res) {
        setPhase(evidence.length > 0 ? "documents" : "response");
      }
    }
  };

  const currentStepNumber = ((): 0 | 1 | 2 | 3 | 4 | 5 => {
    if (phase === "understand" || phase === "requests") return 0;
    if (phase === "questions") return 1;
    if (phase === "documents") return 2;
    if (phase === "response") return 3;
    if (phase === "review") return 4;
    return 5; // act
  })();

  const handleStepSelect = (step: 0 | 1 | 2 | 3 | 4 | 5) => {
    if (step === 0) setPhase("understand");
    else if (step === 1 && hasQuestions) setPhase("questions");
    else if (step === 2) setPhase("documents");
    else if (step === 3) {
      if (!result && id) resolveWorkflow(answers).then(() => setPhase("response"));
      else setPhase("response");
    } else if (step === 4) setPhase("review");
    else if (step === 5 && reviewApproved) setPhase("act");
  };

  if (error) return <div className="app-page"><div className="app-empty" role="alert">{error}</div></div>;
  if (!contract) return <div className="app-page"><div className="app-loading">LOADING WORKFLOW CONTRACT...</div></div>;

  const activeEvidence = mappedEvidence.length > 0 ? mappedEvidence : evidence;
  const section = contract.notice.section ?? "142(1)";
  const officialUrl = contract.officialPortalUrl;

  return (
    <WorkflowLayout
      currentStep={currentStepNumber}
      notice={contract.notice}
      noticeId={id}
      onStepSelect={handleStepSelect}
    >
      <NoticeFactsCard notice={contract.notice} />

      {/* Boundary Mode: Safe stop or explanation only */}
      {(capability === "SAFE_STOP" || capability === "EXPLANATION_ONLY") && (
        <ScreenFrame
          whereAmI="Step 01 · Boundary"
          whatDoesThisMean={title}
          whatDoINeedToDo="Review what was identified, the boundary explanation, and official next steps."
          statusBadge={<CapabilityBadge capability={capability} locale={locale} />}
          secondaryAction={<Link to="/notices" className="app-back-link">← {locale === "hi" ? "सभी नोटिस" : "All notices"}</Link>}
        >
          <div className="space-y-6">
            <ContractExplanation
              capability={capability}
              title={title}
              reason={contract.reason}
              notice={contract.notice}
              requests={requests}
              nextSteps={contract.nextSteps}
              originalText={contract.notice.official_text}
              locale={locale}
            />
            <ContractEvidence evidence={evidence} locale={locale} />
            <CapabilityBoundary
              capability={capability}
              reason={contract.reason}
              nextSteps={contract.nextSteps}
              locale={locale}
            />
          </div>
        </ScreenFrame>
      )}

      {/* Guided Workflow Phases */}
      {(capability === "SUPPORTED" || capability === "PARTIAL_SUPPORT") && (
        <>
          {/* Phase 1: Understand */}
          {(phase === "understand" || phase === "requests") && (
            <ScreenFrame
              whereAmI="Step 01 · Understand"
              whatDoesThisMean={title}
              whatDoINeedToDo={
                capability === "SUPPORTED"
                  ? "Review what was identified, the original communication, and any deadline before choosing the next step."
                  : "Review the extracted facts and follow only the next steps supported by this communication."
              }
              statusBadge={<CapabilityBadge capability={capability} locale={locale} />}
              primaryAction={
                <PrimaryButton onClick={() => setPhase(hasQuestions ? "questions" : "documents")}>
                  {locale === "hi" ? "आगे बढ़ें →" : "Continue →"}
                </PrimaryButton>
              }
              secondaryAction={<Link to="/notices" className="app-back-link">← {locale === "hi" ? "सभी नोटिस" : "All notices"}</Link>}
            >
              <div className="space-y-6">
                <ContractExplanation
                  capability={capability}
                  title={title}
                  reason={contract.reason}
                  notice={contract.notice}
                  requests={requests}
                  nextSteps={contract.nextSteps}
                  originalText={contract.notice.official_text}
                  locale={locale}
                />
                {requests.length > 0 && (
                  <ContractRequests requests={requests} locale={locale} />
                )}
                {!requests.length && (
                  <div className="universal-section">
                    <p className="app-lead">This communication does not contain a separate request schedule. Review its figures and dates before continuing.</p>
                  </div>
                )}
              </div>
            </ScreenFrame>
          )}

          {/* Phase 2: Questions */}
          {phase === "questions" && visibleQuestion && (
            <ScreenFrame
              whereAmI={`Step 02 · Question ${questionIndex + 1} of ${visibleQuestions.length}`}
              whatDoesThisMean={questionText(visibleQuestion)}
              whatDoINeedToDo="Select the option that best matches your records. Your answer determines how Tax Mitra structures your response."
              statusBadge={<CapabilityBadge capability={capability} locale={locale} />}
              secondaryAction={
                <button
                  type="button"
                  onClick={() => {
                    if (questionIndex > 0) {
                      setQuestionIndex(questionIndex - 1);
                    } else {
                      setPhase("understand");
                    }
                  }}
                  className="app-back-link"
                >
                  ← {questionIndex > 0 ? (locale === "hi" ? "पिछला सवाल" : "Previous question") : (locale === "hi" ? "नोटिस अवलोकन" : "Back to overview")}
                </button>
              }
            >
              <div className="universal-section">
                <ContractQuestion
                  question={visibleQuestion}
                  locale={locale}
                  value={answers[visibleQuestion.id]}
                  onChange={(value) => setAnswers({ ...answers, [visibleQuestion.id]: value })}
                  onContinue={handleQuestionContinue}
                />
              </div>
            </ScreenFrame>
          )}

          {/* Phase 3: Documents / Evidence */}
          {phase === "documents" && (
            <ScreenFrame
              whereAmI="Step 03 · Documents"
              whatDoesThisMean={locale === "hi" ? "ज़रूरी रिकॉर्ड और प्रमाण" : "Required Records & Evidence"}
              whatDoINeedToDo={locale === "hi" ? "अपने उत्तर के समर्थन के लिए आवश्यक दस्तावेज़ तैयार रखें।" : "Gather these records before writing your response. Required items are what the notice specifically asked for."}
              statusBadge={<CapabilityBadge capability={capability} locale={locale} />}
              primaryAction={
                <PrimaryButton
                  onClick={async () => {
                    if (!result) await resolveWorkflow(answers);
                    setPhase("response");
                  }}
                >
                  {locale === "hi" ? "उत्तर तैयार करें →" : "Continue to response →"}
                </PrimaryButton>
              }
              secondaryAction={
                <button
                  type="button"
                  onClick={() => {
                    if (hasQuestions) {
                      setPhase("questions");
                      setQuestionIndex(visibleQuestions.length - 1);
                    } else {
                      setPhase("understand");
                    }
                  }}
                  className="app-back-link"
                >
                  ← {locale === "hi" ? "सवालों पर वापस" : "Back to questions"}
                </button>
              }
            >
              <div className="space-y-6">
                <ContractEvidence evidence={activeEvidence} locale={locale} />
              </div>
            </ScreenFrame>
          )}

          {/* Phase 4: Editable Response Draft */}
          {phase === "response" && (
            <ScreenFrame
              whereAmI="Step 04 · Response"
              whatDoesThisMean={locale === "hi" ? "अपना उत्तर तैयार करें" : "Your prepared response"}
              whatDoINeedToDo={locale === "hi" ? "Tax Mitra ने नीचे एक उत्तर का मसौदा तैयार किया है। आप इसे अपनी जानकारी के अनुसार बदल सकते हैं। कोई भी जमा नहीं किया गया है।" : "Tax Mitra has drafted a response based on your answers. Edit it to match your exact records. Nothing has been submitted."}
              statusBadge={<CapabilityBadge capability={capability} locale={locale} />}
              primaryAction={
                <PrimaryButton onClick={() => setPhase("review")}>
                  {locale === "hi" ? "समीक्षा करें →" : "Review & approve →"}
                </PrimaryButton>
              }
              secondaryAction={
                <button
                  type="button"
                  onClick={() => setPhase(activeEvidence.length > 0 ? "documents" : "questions")}
                  className="app-back-link"
                >
                  ← {locale === "hi" ? "दस्तावेज़ों पर वापस" : "Back to documents"}
                </button>
              }
            >
              <div className="universal-section">
                <p className="app-section-label">[ EDITABLE DRAFT — NOT SUBMITTED ]</p>
                <h2 className="question-title">{locale === "hi" ? "उत्तर का मसौदा" : "Response draft"}</h2>
                <p className="app-body" style={{ marginBottom: 16 }}>
                  {locale === "hi"
                    ? "नीचे दिए गए मसौदे को संपादित करें। केवल तथ्यात्मक जानकारी जोड़ें — Tax Mitra कोई कानूनी दावा नहीं करता।"
                    : "Edit the draft below. Add only factual information from your records. Tax Mitra does not make legal claims on your behalf."}
                </p>
                <textarea
                  className="response-draft-editor"
                  value={editableDraft}
                  onChange={(e) => setEditableDraft(e.target.value)}
                  rows={Math.max(14, editableDraft.split("\n").length + 2)}
                  spellCheck={false}
                  aria-label="Editable response draft"
                />
                <p className="app-caption" style={{ marginTop: 8, color: "var(--tm-muted)", fontSize: 12 }}>
                  {locale === "hi"
                    ? "यह मसौदा केवल आपके डिवाइस पर है। Tax Mitra ने कुछ भी विभाग को नहीं भेजा है।"
                    : "This draft exists only on your device. Tax Mitra has not sent anything to the Income Tax Department."}
                </p>
                {editableDraft && (
                  <ResponseDownloadToolbar draft={editableDraft} notice={contract.notice} locale={locale} />
                )}
              </div>
            </ScreenFrame>
          )}

          {/* Phase 5: Review & Approve */}
          {phase === "review" && (
            <ScreenFrame
              whereAmI="Step 05 · Review"
              whatDoesThisMean={locale === "hi" ? "आधिकारिक जमा करने से पहले समीक्षा करें" : "Review before any official submission"}
              whatDoINeedToDo={locale === "hi" ? "मूल नोटिस, आपके उत्तर और तैयार मसौदे को ध्यान से पढ़ें। अनुमोदन के बाद ही अगला चरण उपलब्ध होगा।" : "Read the original notice wording, your answers, and the prepared draft carefully. Check everything before approving."}
              statusBadge={<CapabilityBadge capability={capability} locale={locale} />}
              secondaryAction={
                <button type="button" onClick={() => setPhase("response")} className="app-back-link">
                  ← {locale === "hi" ? "उत्तर पर वापस" : "Back to response"}
                </button>
              }
            >
              <div className="universal-section">
                <p className="app-section-label">[ HUMAN REVIEW REQUIRED ]</p>
                <h2 className="question-title">{locale === "hi" ? "समीक्षा और अनुमोदन" : "Review & approval"}</h2>
                <p className="app-body">
                  {locale === "hi"
                    ? "Tax Mitra ने कुछ भी जमा नहीं किया है। नीचे मूल नोटिस और आपका तैयार उत्तर देखें।"
                    : "Tax Mitra has not submitted anything. Review the original notice wording and your prepared response below before approving."}
                </p>

                {/* Original notice wording */}
                {contract.notice.official_text && (
                  <details className="review-section" style={{ marginTop: 20 }}>
                    <summary className="review-section-title">{locale === "hi" ? "मूल नोटिस की भाषा" : "Original notice wording"}</summary>
                    <blockquote className="review-original-text">{contract.notice.official_text}</blockquote>
                  </details>
                )}

                {/* Prepared draft (read-only preview) */}
                {editableDraft && (
                  <div style={{ marginTop: 20 }}>
                    <p className="app-section-label">{locale === "hi" ? "आपका तैयार उत्तर" : "YOUR PREPARED RESPONSE"}</p>
                    <pre className="review-draft-preview">{editableDraft}</pre>
                    <ResponseDownloadToolbar draft={editableDraft} notice={contract.notice} locale={locale} />
                  </div>
                )}

                <label className="review-approve-label">
                  <input
                    type="checkbox"
                    checked={reviewApproved}
                    onChange={(e) => setReviewApproved(e.target.checked)}
                  />
                  <span>
                    {locale === "hi"
                      ? "मैंने मूल नोटिस, उपयोग की गई जानकारी और तैयार उत्तर की समीक्षा कर ली है। आधिकारिक प्रस्तुतीकरण मेरी ज़िम्मेदारी है।"
                      : "I have reviewed the original notice, my answers, and the prepared response. Official submission is my responsibility."}
                  </span>
                </label>

                <div style={{ marginTop: 20 }}>
                  <PrimaryButton
                    onClick={() => { if (reviewApproved) setPhase("act"); }}
                  >
                    {reviewApproved
                      ? (locale === "hi" ? "पोर्टल पर जमा करने के चरण देखें →" : "See portal submission steps →")
                      : (locale === "hi" ? "पहले ऊपर समीक्षा करें" : "Review above to continue")}
                  </PrimaryButton>
                </div>
              </div>
            </ScreenFrame>
          )}

          {/* Phase 6: Act — Portal Navigation Guide */}
          {phase === "act" && (
            <ScreenFrame
              whereAmI="Step 06 · Act"
              whatDoesThisMean={locale === "hi" ? "आधिकारिक पोर्टल पर अपना उत्तर जमा करें" : "Submit your response on the official portal"}
              whatDoINeedToDo={locale === "hi" ? "नीचे दिए गए चरणों का पालन करें। Tax Mitra ने कुछ भी जमा नहीं किया है — यह आपकी ज़िम्मेदारी है।" : "Follow the steps below on the Income Tax e-Filing portal. Tax Mitra has not submitted anything — this is your action."}
              statusBadge={<CapabilityBadge capability={capability} locale={locale} />}
              secondaryAction={
                <button type="button" onClick={() => setPhase("review")} className="app-back-link">
                  ← {locale === "hi" ? "समीक्षा पर वापस" : "Back to review"}
                </button>
              }
            >
              <div className="universal-section">
                <p className="app-section-label">[ PORTAL NAVIGATION GUIDE ]</p>
                <h2 className="question-title">{locale === "hi" ? "e-Filing पोर्टल पर उत्तर कैसे जमा करें" : "How to submit your response on the e-Filing portal"}</h2>
                <p className="app-body" style={{ marginBottom: 20 }}>
                  {locale === "hi"
                    ? "Tax Mitra ने आपका उत्तर तैयार किया है। अब आपको इसे आधिकारिक Income Tax e-Filing पोर्टल पर जमा करना है।"
                    : `Tax Mitra has prepared your response for notice under ${section}. You must now submit it on the official Income Tax e-Filing portal.`}
                </p>

                <ol className="act-steps-list">
                  <li className="act-step">
                    <span className="act-step-num">1</span>
                    <div>
                      <strong>{locale === "hi" ? "पोर्टल खोलें और लॉगिन करें" : "Open the portal and log in"}</strong>
                      <p>{locale === "hi" ? "incometax.gov.in पर जाएं। अपने PAN और पासवर्ड से लॉगिन करें।" : "Go to incometax.gov.in and log in with your PAN and password."}</p>
                      <a href={officialUrl} target="_blank" rel="noreferrer" className="act-portal-link">
                        {locale === "hi" ? "e-Filing पोर्टल खोलें ↗" : "Open e-Filing portal ↗"}
                      </a>
                    </div>
                  </li>
                  <li className="act-step">
                    <span className="act-step-num">2</span>
                    <div>
                      <strong>{locale === "hi" ? "e-Proceedings पर जाएं" : "Navigate to e-Proceedings"}</strong>
                      <p>{locale === "hi"
                        ? "लॉगिन के बाद: Pending Actions → e-Proceedings पर क्लिक करें।"
                        : "After login: Click Pending Actions → e-Proceedings in the top menu."}</p>
                    </div>
                  </li>
                  <li className="act-step">
                    <span className="act-step-num">3</span>
                    <div>
                      <strong>{locale === "hi" ? "अपना नोटिस खोजें" : "Find your notice"}</strong>
                      <p>{locale === "hi"
                        ? `धारा ${section} के अंतर्गत आपका नोटिस सूची में दिखेगा। नोटिस संदर्भ देखें: ${contract.notice.official_reference ?? "—"}`
                        : `Your notice under section ${section} will appear in the list. Look for reference: ${contract.notice.official_reference ?? "—"}`}</p>
                    </div>
                  </li>
                  <li className="act-step">
                    <span className="act-step-num">4</span>
                    <div>
                      <strong>{locale === "hi" ? "\"Submit Response\" पर क्लिक करें" : "Click \"Submit Response\""}</strong>
                      <p>{locale === "hi"
                        ? "नोटिस के बगल में Submit Response / Comply पर क्लिक करें।"
                        : "Click Submit Response or Comply next to your notice. This opens the official response form."}</p>
                    </div>
                  </li>
                  <li className="act-step">
                    <span className="act-step-num">5</span>
                    <div>
                      <strong>{locale === "hi" ? "अपना तैयार उत्तर पेस्ट करें" : "Paste your prepared response"}</strong>
                      <p>{locale === "hi"
                        ? "Tax Mitra का तैयार मसौदा नीचे देखें और उसे पोर्टल के टेक्स्ट बॉक्स में पेस्ट करें।"
                        : "Copy your prepared response from Tax Mitra (shown below) and paste it into the portal's text field."}</p>
                      {editableDraft && (
                        <>
                          <pre className="act-draft-copy">{editableDraft}</pre>
                          <ResponseDownloadToolbar draft={editableDraft} notice={contract.notice} locale={locale} />
                        </>
                      )}
                    </div>
                  </li>
                  <li className="act-step">
                    <span className="act-step-num">6</span>
                    <div>
                      <strong>{locale === "hi" ? "दस्तावेज़ अपलोड करें" : "Upload your supporting documents"}</strong>
                      <p>{locale === "hi"
                        ? "Documents चरण में सूचीबद्ध आवश्यक रिकॉर्ड अपलोड करें। सुनिश्चित करें कि सभी आवश्यक दस्तावेज़ शामिल हैं।"
                        : "Upload the required records listed in your Documents step. Make sure all required items are attached before submitting."}</p>
                    </div>
                  </li>
                  <li className="act-step">
                    <span className="act-step-num">7</span>
                    <div>
                      <strong>{locale === "hi" ? "डिजिटल हस्ताक्षर करें और जमा करें" : "e-Verify and submit"}</strong>
                      <p>{locale === "hi"
                        ? "Aadhaar OTP, Net Banking, या DSC से सत्यापित करें। जमा करने के बाद पोर्टल से acknowledgement डाउनलोड करें।"
                        : "Verify using Aadhaar OTP, Net Banking, or DSC. After submitting, download the acknowledgement from the portal."}</p>
                    </div>
                  </li>
                </ol>

                <div className="act-boundary-note">
                  <p>
                    <strong>{locale === "hi" ? "⚠ महत्वपूर्ण" : "⚠ Important"}</strong>
                    {" "}
                    {locale === "hi"
                      ? "Tax Mitra ने आपकी ओर से कुछ भी जमा नहीं किया है। आधिकारिक पोर्टल पर सबमिट करना पूरी तरह आपकी ज़िम्मेदारी है। किसी भी कानूनी अनिश्चितता के लिए कर-विशेषज्ञ से सलाह लें।"
                      : "Tax Mitra has not submitted anything on your behalf. Submitting on the official portal is entirely your responsibility. For any legal uncertainty, consult a qualified tax professional."}
                  </p>
                </div>

                <div style={{ marginTop: 20 }}>
                  <a
                    className="app-primary inline-block"
                    href={officialUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {locale === "hi" ? "e-Filing पोर्टल खोलें ↗" : "Open e-Filing portal ↗"}
                  </a>
                </div>
              </div>
            </ScreenFrame>
          )}
        </>
      )}
    </WorkflowLayout>
  );
}
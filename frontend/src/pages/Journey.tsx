import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../i18n";
import { api, EvidenceRecommendation, NoticeCard, Question, QuestionAnswer, ScrutinyRequest, UniversalWorkflowContract, WorkflowCapability, verifiedIncomeTaxUrl, OFFICIAL_EFILING_PORTAL_URL } from "../lib";
import { CapabilityBadge, CapabilityBoundary, ContractEvidence, ContractExplanation, ContractQuestion } from "../components/UniversalWorkflow";
import { NoticeFactsCard, PrimaryButton, ScreenFrame, WorkflowLayout } from "../components";

function userCapability(value: string | undefined): WorkflowCapability {
  return value === "SUPPORTED" || value === "PARTIAL_SUPPORT" || value === "EXPLANATION_ONLY" || value === "SAFE_STOP" ? value : "SAFE_STOP";
}

function questionText(question: Question): string { return question.text || "Please review this question."; }
function normalizeQuestion(question: Question & { question_id?: string; question?: string; why_we_are_asking?: string; type?: Question["question_type"] }): Question {
  return { id: question.id || question.question_id || "", text: question.text || question.question || "", help: question.help || question.why_we_are_asking || "", options: question.options || [], question_type: question.question_type || question.type, required: question.required, conditions: question.conditions, related_request_ids: question.related_request_ids };
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

export default function Journey() {
  const { id = "" } = useParams();
  const { locale } = useI18n();
  const [contract, setContract] = useState<UniversalWorkflowContract | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [requests, setRequests] = useState<ScrutinyRequest[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRecommendation[]>([]);
  const [answers, setAnswers] = useState<Record<string, QuestionAnswer>>({});
  const [questionIndex, setQuestionIndex] = useState(0);
  const [phase, setPhase] = useState<"understand" | "questions" | "evidence" | "review">("understand");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [reviewApproved, setReviewApproved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([api.notice(id), api.noticeWorkflow(id)]).then(async ([notice, routed]) => {
      const capability = userCapability(routed.workflow?.capability ?? routed.classification.capability);
      const backend = routed.contract;
      const base: UniversalWorkflowContract = { workflowId: routed.classification.workflow_id, category: routed.classification.category, title: routed.workflow?.title ?? notice.title, capability, confidence: routed.classification.confidence, groundingStatus: routed.classification.grounding_status, reason: routed.classification.reason, notice, requests: backend?.requests ?? [], questions: (backend?.questions ?? []).map(normalizeQuestion), evidence: backend?.evidence ?? [], action: backend?.action, nextSteps: backend?.next_steps ?? ["Review the original communication and its deadline.", "Use the official Income Tax e-Filing portal for any required action."], officialPortalUrl: verifiedIncomeTaxUrl(backend?.official_portal.url ?? OFFICIAL_EFILING_PORTAL_URL) };
      setContract(base);
      if (routed.contract) { setRequests(routed.contract.requests ?? []); setEvidence(routed.contract.evidence ?? []); setQuestions((routed.contract.questions ?? []).map(normalizeQuestion)); }
      if (capability === "SAFE_STOP" || capability === "EXPLANATION_ONLY") return;
      if (routed.contract?.questions?.length || routed.contract?.requests?.length) return;
      const workflowData = await api.workflowData(id, locale, base.workflowId);
      setRequests(workflowData.requests); setEvidence(workflowData.evidence); setQuestions(workflowData.questions);
    }).catch(() => setError("We could not load this workflow contract."));
  }, [id, locale]);

  const currentQuestion = questions[questionIndex];
  const visibleQuestions = questions.filter((question) => questionIsVisible(question, answers));
  const visibleQuestion = visibleQuestions[questionIndex];
  const hasQuestions = visibleQuestions.length > 0;
  const capability = contract?.capability ?? "SAFE_STOP";
  const title = contract?.title[locale] ?? contract?.title.en ?? "Income Tax communication";
  const responseDraft = typeof result?.draft === "string" ? result.draft : "";
  const checklist = Array.isArray(result?.checklist) ? result.checklist as { title?: Record<string, string>; why_needed?: Record<string, string> }[] : [];
  const questionAnswer = (value: QuestionAnswer) => {
    if (!visibleQuestion) return;
    const next = { ...answers, [visibleQuestion.id]: value }; setAnswers(next);
    if (questionIndex + 1 < visibleQuestions.length) setQuestionIndex(questionIndex + 1);
    else {
      const call = api.resolveWorkflow(id, contract?.workflowId ?? "", next);
      call.then((response) => { setResult(response as unknown as Record<string, unknown>); setPhase(evidence.length > 0 ? "evidence" : "review"); }).catch(() => setError("We could not resolve this workflow safely."));
    }
  };
  if (error) return <div className="app-page"><div className="app-empty" role="alert">{error}</div></div>;
  if (!contract) return <div className="app-page"><div className="app-loading">LOADING WORKFLOW CONTRACT...</div></div>;

  return <WorkflowLayout currentStep={phase === "understand" ? 0 : phase === "questions" ? 2 : phase === "evidence" ? 3 : 4} notice={contract.notice} noticeId={id}>
    <NoticeFactsCard notice={contract.notice} />
    <ScreenFrame whereAmI={`Step ${phase === "understand" ? "01" : phase === "questions" ? "03" : phase === "evidence" ? "04" : "06"} · ${phase}`} whatDoesThisMean={title} whatDoINeedToDo={capability === "SUPPORTED" ? "Review the communication, answer only the questions that change the action path, and approve the result before using the official portal." : "Review the extracted facts and follow only the next steps supported by this communication."} statusBadge={<CapabilityBadge capability={capability} locale={locale} />} secondaryAction={<Link to="/notices" className="app-back-link">← All notices</Link>}>
      <div className="space-y-6">
        {(capability === "SAFE_STOP" || capability === "EXPLANATION_ONLY") && <><ContractExplanation capability={capability} title={title} reason={contract.reason} notice={contract.notice} requests={requests} nextSteps={contract.nextSteps} originalText={contract.notice.official_text} locale={locale} /><ContractEvidence evidence={evidence} locale={locale} /><CapabilityBoundary capability={capability} reason={contract.reason} nextSteps={contract.nextSteps} locale={locale} /></>}
        {(capability === "SUPPORTED" || capability === "PARTIAL_SUPPORT") && phase === "understand" && <><ContractExplanation capability={capability} title={title} reason={contract.reason} notice={contract.notice} requests={requests} nextSteps={contract.nextSteps} originalText={contract.notice.official_text} locale={locale} />{!requests.length && <div className="universal-section"><p className="app-lead">This communication does not contain a separate request schedule. Review its figures and dates before continuing.</p></div>}<PrimaryButton onClick={() => setPhase(hasQuestions ? "questions" : "evidence")}>Continue →</PrimaryButton></>}
        {(capability === "SUPPORTED" || capability === "PARTIAL_SUPPORT") && phase === "questions" && visibleQuestion && <div className="universal-section"><p className="app-section-label">Question {questionIndex + 1} of {visibleQuestions.length}</p><h2 className="question-title">{questionText(visibleQuestion)}</h2><p className="app-body">{visibleQuestion.help}</p><ContractQuestion question={visibleQuestion} locale={locale} value={answers[visibleQuestion.id]} onChange={(value) => setAnswers({ ...answers, [visibleQuestion.id]: value })} onContinue={() => questionAnswer(answers[visibleQuestion.id] ?? "")} /></div>}
        {(capability === "SUPPORTED" || capability === "PARTIAL_SUPPORT") && phase === "evidence" && <><ContractEvidence evidence={evidence} locale={locale} /><PrimaryButton onClick={() => setPhase("review")}>Continue to review →</PrimaryButton></>}
        {(capability === "SUPPORTED" || capability === "PARTIAL_SUPPORT") && phase === "review" && <div className="universal-section"><p className="app-section-label">[ HUMAN REVIEW REQUIRED ]</p><h2 className="question-title">Review before any official action</h2><p className="app-body">Tax Mitra has not submitted anything. Check the original wording, answers, missing evidence, and prepared action before continuing on the official portal.</p>{responseDraft && <div className="original-source"><p className="app-section-label">PREPARED RESPONSE / ACTION</p><pre className="whitespace-pre-wrap">{responseDraft}</pre></div>}{checklist.length > 0 && <div className="mt-5"><p className="app-section-label">EVIDENCE CHECKLIST</p><ul className="list-disc pl-5">{checklist.map((item, index) => <li key={index}>{item.title?.[locale] ?? item.title?.en ?? "Required record"}{item.why_needed?.[locale] || item.why_needed?.en ? ` — ${item.why_needed?.[locale] ?? item.why_needed?.en}` : ""}</li>)}</ul></div>}<label className="flex gap-3 items-start mt-6 text-sm"><input type="checkbox" checked={reviewApproved} onChange={(event) => setReviewApproved(event.target.checked)} /><span>I have reviewed the original notice, information used, and prepared action. Official submission remains my responsibility.</span></label><a className={`app-primary inline-block mt-5 ${!reviewApproved ? "pointer-events-none opacity-50" : ""}`} aria-disabled={!reviewApproved} href={reviewApproved ? contract.officialPortalUrl : undefined} target={reviewApproved ? "_blank" : undefined} rel="noreferrer">Open official portal ↗</a></div>}
      </div>
    </ScreenFrame>
  </WorkflowLayout>;
}

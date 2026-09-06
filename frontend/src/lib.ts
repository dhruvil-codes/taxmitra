// API client + journey state persistence (localStorage).

export type Locale = "en" | "hi";

export const OFFICIAL_EFILING_PORTAL_URL = "https://www.incometax.gov.in/iec/foportal/";

export function verifiedIncomeTaxUrl(url: string): string {
  try {
    const candidate = new URL(url);
    if (candidate.hostname === "www.incometax.gov.in" && candidate.pathname.startsWith("/iec/forservices")) {
      return OFFICIAL_EFILING_PORTAL_URL;
    }
  } catch {
    return url;
  }
  return url;
}

export interface Citizen {
  id: string;
  name: string;
  pan_masked: string;
  city: string;
  preferred_locale: Locale;
  profile_note: Record<string, string>;
}

export interface NoticeCard {
  id: string;
  section: string;
  category: string;
  supported: boolean;
  title: Record<string, string>;
  amount_in_question: number;
  issue_date: string;
  assessment_year: string;
  due_date: string | null;
  days_remaining: number | null;
  status: string;
  official_text?: string;
  income_source?: string;
  official_reference?: string;
  citizen_id?: string;
  workflow_id?: string;
  workflow_status?: "supported" | "partial_support" | "safe_stop";
  capability?: "SUPPORTED" | "PARTIAL_SUPPORT" | "EXPLANATION_ONLY" | "SAFE_STOP";
  classification_confidence?: number;
  classification_grounding_status?: string;
  frontend_entry?: "journey" | "scrutiny" | "unsupported";
}

export interface WorkflowDefinition {
  workflow_id: string;
  category: string;
  title: Record<string, string>;
  classification_signals: string[];
  required_facts: string[];
  question_plan: string;
  evidence: string;
  response_action: string;
  refusal_conditions: string[];
  supported: boolean;
  implementation: string;
  frontend_entry: "journey" | "scrutiny" | "unsupported";
  capability: "SUPPORTED" | "PARTIAL_SUPPORT" | "EXPLANATION_ONLY" | "SAFE_STOP";
  status: "supported" | "partial_support" | "safe_stop";
}

export interface WorkflowClassification {
  workflow_id: string;
  category: string;
  confidence: number;
  grounding_status: string;
  supported: boolean;
  status: "supported" | "partial_support" | "safe_stop";
  capability?: "SUPPORTED" | "PARTIAL_SUPPORT" | "EXPLANATION_ONLY" | "SAFE_STOP";
  reason: string;
}

export type WorkflowCapability = "SUPPORTED" | "PARTIAL_SUPPORT" | "EXPLANATION_ONLY" | "SAFE_STOP";

export interface UniversalWorkflowContract {
  workflowId: string;
  category: string;
  title: Record<string, string>;
  capability: WorkflowCapability;
  confidence: number;
  groundingStatus: string;
  reason: string;
  notice: NoticeCard;
  requests: ScrutinyRequest[];
  questions: Question[];
  evidence: EvidenceRecommendation[];
  action?: string;
  safeStopReason?: string;
  nextSteps: string[];
  officialPortalUrl: string;
}

export interface BackendWorkflowContract {
  identity: { workflow_id: string; category: string; title: Record<string, string> };
  capability: WorkflowCapability;
  confidence: number;
  grounding_status: string;
  reason: string;
  notice_facts: Record<string, string | number | null | undefined>;
  requests: ScrutinyRequest[];
  questions: (Question & { question_id?: string; question?: string; why_we_are_asking?: string; type?: Question["question_type"] })[];
  evidence: EvidenceRecommendation[];
  safe_stop: { reason: string; facts: Record<string, string | number | null | undefined> };
  official_portal: { url: string; submission_boundary: string };
}

export interface UniversalExtractionResult {
  supported: boolean;
  status: "safe_stop" | "needs_confirmation";
  metadata: Record<string, string | null>;
  extraction: {
    status: string;
    confidence: number;
    warnings: string[];
    refusal_reason: string | null;
    method: "text" | "ocr" | "mixed" | "none";
    page_count: number;
  };
  classification: WorkflowClassification;
  workflow: WorkflowDefinition | null;
  pages: { page_number: number; text: string; source: string }[];
  extraction_id?: string;
  fingerprint?: string;
  requires_human_confirmation?: boolean;
  requests?: ScrutinyRequest[];
  document?: { status: string; page_count: number; sha256: string; pages: { page_number: number; text: string; source: string }[] };
}

export interface Citation {
  id: string;
  section: string;
  title: string;
  source_name: string;
  official_url: string;
  accessed_date: string;
  verification: string;
  verification_status?: string;
  verification_state?: "Verified" | "Pending verification" | "Not applicable" | "Unknown";
  verified_date?: string;
  page_location?: string;
  summary?: string;
  applicability?: string;
  effective_period?: string;
  why_supports?: string;
  excerpt: string;
}

export interface Explanation {
  content: {
    plain_language: string;
    what_this_does_not_mean: string;
    possible_reasons: string[];
  };
  citations: Citation[];
  scope_statement: Record<string, string>;
  source: string;
  degraded: boolean;
  demo_mode: boolean;
}

export interface Question {
  id: string;
  text: string;
  help: string;
  options: { id: string; label: string }[];
  question_type?: QuestionType;
  required?: boolean;
  conditions?: QuestionCondition[];
  related_request_ids?: string[];
}

export interface QuestionCondition {
  depends_on?: string;
  question_id?: string;
  equals?: string;
  value?: string;
  one_of?: string[];
  values?: string[];
}

export type QuestionType = "single_choice" | "multi_choice" | "choice_with_other" | "text" | "yes_no" | "number" | "date" | "multiple_choice" | "free_text" | "document_availability" | "confirmation";

export interface ResolveResult {
  supported: boolean;
  path?: {
    path_id: string;
    position: string;
    headline: Record<string, string>;
    guidance: Record<string, string>;
  };
  checklist?: { id: string; title: Record<string, string>; why_needed: Record<string, string> }[];
  deadline?: { due_date: string | null; days_remaining: number | null; status: string };
  draft?: string;
  official_step?: {
    label: Record<string, string>;
    url: string;
    boundary: Record<string, string>;
  };
  // refusal payload fields
  headline?: Record<string, string>;
  why?: Record<string, string>;
  suggestion?: Record<string, string>;
  official_links?: { label: Record<string, string>; url: string }[];
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(url: string, status: number, detail: unknown) {
    let message: string;
    if (typeof detail === "string") {
      message = detail;
    } else if (detail && typeof detail === "object") {
      if ("detail" in detail) {
        message = String((detail as { detail: unknown }).detail);
      } else if ("error" in detail) {
        message = String((detail as { error: unknown }).error);
      } else if ("message" in detail) {
        message = String((detail as { message: unknown }).message);
      } else {
        message = `${url} -> ${status}`;
      }
    } else {
      message = `${url} -> ${status}`;
    }
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export interface Grounding {
  method: string;
  confidence: number;
  below_floor: boolean;
  verified_source_count?: number;
  verified?: boolean;
}

export interface ScrutinyRequest {
  id: string;
  request_id: string;
  classification_id: string;
  original_text: string;
  plain_language_explanation: Record<string, string>;
  why_required: Record<string, string>;
  required_evidence: Record<string, string>[];
  what_department_is_asking?: string;
  expected_evidence?: Record<string, string>[];
  response_section: string;
  citations: Citation[];
  confidence: number;
  warnings: string[];
  grounding?: Grounding;
  page_number?: number;
  source_location?: string;
  category?: string;
  clarifying_questions?: { id: string; text: Record<string, string> }[];
  status?: "not_started" | "need_information" | "documents_needed" | "ready_for_response" | "reviewed";
  workflow_status?: "not_started" | "need_information" | "documents_needed" | "ready_for_response" | "reviewed";
  sources?: Citation[];
}

export interface ExtractionResult {
  supported: boolean;
  metadata: {
    notice_reference: string | null;
    section: string | null;
    assessment_year: string | null;
    response_deadline: string | null;
    issue_date: string | null;
  };
  requests: ScrutinyRequest[];
  extraction: {
    status: "uploaded" | "extracted" | "needs_confirmation" | "confirmed" | "unsupported" | "refused";
    confidence: number;
    warnings: string[];
    refusal_reason: string | null;
    error_code?: string | null;
    method?: "text" | "ocr" | "mixed" | "none";
    page_count?: number;
  };
  grounding?: Grounding;
  extraction_id?: string;
  fingerprint?: string;
  requires_human_confirmation?: boolean;
  document?: { status: string; page_count: number; sha256: string; pages: { page_number: number; text: string; source: string }[] };
}

export interface ExtractionConfirmationResult {
  supported: boolean;
  status: "confirmed" | "refused";
  extraction_id?: string;
  notice_id?: string;
  requests?: ScrutinyRequest[];
  reason?: string;
}

export interface ScrutinyRequestsResult {
  supported: boolean;
  notice_id?: string;
  extraction?: { source_type: string; requires_human_confirmation: boolean; confirmed: boolean };
  requests?: ScrutinyRequest[];
  evidence?: EvidenceRecommendation[];
  grounding?: { method: string; confidence: number; below_floor: boolean };
  headline?: Record<string, string>;
  why?: Record<string, string>;
  suggestion?: Record<string, string>;
  official_links?: { label: Record<string, string>; url: string }[];
}

export interface MinimumQuestion {
  question_id: string;
  question: string;
  why_we_are_asking: string;
  type: QuestionType;
  options: { id: string; label: string }[];
  related_request_ids: string[];
  required: boolean;
  conditions: Record<string, string>[];
  status: string;
}

export interface MinimumQuestionPlanResult {
  supported: boolean;
  notice_id: string;
  request_count: number;
  question_count: number;
  questions: MinimumQuestion[];
  evidence?: EvidenceRecommendation[];
  grounding?: Grounding;
  headline?: Record<string, string>;
  why?: Record<string, string>;
  suggestion?: Record<string, string>;
  official_links?: { label: Record<string, string>; url: string }[];
}

export interface ScrutinyQuestion extends Question { request_id: string }
export interface ScrutinyChecklistItem {
  id: string;
  request_id: string;
  status: "yes" | "no" | "unsure";
  title: Record<string, string>;
  required_evidence: Record<string, string>[];
  why_needed: Record<string, string>;
  workflow_status?: "need_information" | "documents_needed" | "ready_for_response" | "reviewed";
}

export type EvidenceStatus = "have" | "need_to_find" | "dont_have" | "not_sure";
export interface EvidenceRecommendation {
  request_id: string;
  document_id: string;
  document_name: Record<string, string>;
  reason: Record<string, string>;
  requirement_level: "required" | "possibly_relevant";
  required_or_possibly_relevant?: "required" | "possibly_relevant";
  source: string[];
  status: EvidenceStatus;
}
export interface ScrutinyResolveResult extends Omit<ResolveResult, "checklist" | "path"> {
  category: string;
  path?: { path_id: "ready_to_respond" | "needs_evidence" | "needs_review"; headline: Record<string, string>; professional_help_recommended: boolean };
  checklist?: ScrutinyChecklistItem[];
  evidence?: EvidenceRecommendation[];
  missing_evidence?: EvidenceRecommendation[];
  safety_review?: { status: "ready" | "blocked"; ready: boolean; checks: { key: string; label: string; status: "passed" | "blocked"; missing: string | null }[]; missing: string[] };
}

function configuredApiBase(value: string | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) return "";
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new Error("VITE_API_BASE_URL must be an absolute http(s) URL");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("VITE_API_BASE_URL must use http:// or https://");
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("VITE_API_BASE_URL must be an API origin without credentials, query, or hash");
  }
  return parsed.origin;
}

const apiBase = configuredApiBase(import.meta.env.VITE_API_BASE_URL);

// Export for debugging in development
if (import.meta.env.DEV) {
  (window as any).__TAXMITRA_API_BASE__ = apiBase;
}

function apiUrl(url: string): string {
  return `${apiBase}${url}`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const fullUrl = apiUrl(url);
  const res = await fetch(fullUrl, init);
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { detail = (await res.json()).detail ?? detail; } catch { /* non-JSON response */ }
    throw new ApiError(url, res.status, detail);
  }
  return res.json();
}

async function get<T>(url: string, signal?: AbortSignal): Promise<T> {
  return request<T>(url, { signal });
}

async function post<T>(url: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return request<T>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

async function loadWorkflowData(id: string, locale: Locale, workflowId: string): Promise<{ requests: ScrutinyRequest[]; evidence: EvidenceRecommendation[]; questions: Question[] }> {
  if (workflowId === "scrutiny_142_1") {
    const [requestData, questionData] = await Promise.all([
      get<ScrutinyRequestsResult>(`/api/scrutiny/${id}/requests?locale=${locale}&extraction_confirmed=true`),
      get<MinimumQuestionPlanResult>(`/api/scrutiny/${id}/question-plan?locale=${locale}&extraction_confirmed=true`),
    ]);
    return { requests: requestData.requests ?? [], evidence: requestData.evidence ?? questionData.evidence ?? [], questions: (questionData.questions ?? []).map((q) => ({ id: q.question_id, text: q.question, help: q.why_we_are_asking, options: q.options, question_type: q.type, required: q.required, conditions: q.conditions, related_request_ids: q.related_request_ids })) };
  }
  const questionData = await get<{ questions: Question[]; requests?: ScrutinyRequest[]; evidence?: EvidenceRecommendation[] }>(`/api/workflow/questions/${id}?locale=${locale}`);
  return { requests: questionData.requests ?? [], evidence: questionData.evidence ?? [], questions: questionData.questions ?? [] };
}

export type QuestionAnswer = string | string[] | { choice: string; other: string };

function resolveWorkflowContract(id: string, workflowId: string, answers: Record<string, QuestionAnswer>): Promise<ResolveResult | ScrutinyResolveResult> {
  return workflowId === "scrutiny_142_1"
    ? post<ScrutinyResolveResult>("/api/scrutiny/resolve-minimum", { notice_id: id, answers, extraction_confirmed: true, document_statuses: {} })
    : post<ResolveResult>("/api/workflow/resolve", { notice_id: id, answers });
}

export const api = {
  citizens: () => get<Citizen[]>("/api/citizens"),
  notices: (citizenId: string) => get<NoticeCard[]>(`/api/notices?citizen_id=${citizenId}`),
  notice: (id: string) => get<NoticeCard>(`/api/notices/${id}`),
  workflows: () => get<{ workflows: WorkflowDefinition[] }>("/api/workflows"),
  noticeWorkflow: (id: string) => get<{ notice_id: string; classification: WorkflowClassification; workflow: WorkflowDefinition | null; contract?: BackendWorkflowContract }>(`/api/notices/${id}/workflow`),
  extractWorkflow: (file: File, signal?: AbortSignal) => {
    const body = new FormData();
    body.append("file", file);
    return request<UniversalExtractionResult>("/api/workflows/extract", { method: "POST", body, signal });
  },
  confirmWorkflowExtraction: (extractionId: string, fingerprint: string, confirmed: boolean, corrections: Record<string, string> = {}, signal?: AbortSignal) =>
    post<{ supported: boolean; status: string; notice_id?: string; frontend_entry?: "journey" | "scrutiny" | "unsupported"; capability?: string }>("/api/workflows/confirm", { extraction_id: extractionId, fingerprint, confirmed, corrections }, signal),
  explanation: (id: string, locale: Locale) =>
    get<Explanation>(`/api/ai/explanation/${id}?locale=${locale}`),
  questions: (id: string, locale: Locale) =>
    get<{ questions: Question[] }>(`/api/workflow/questions/${id}?locale=${locale}`),
  workflowData: loadWorkflowData,
  resolveWorkflow: resolveWorkflowContract,
  resolve: (noticeId: string, answers: Record<string, QuestionAnswer>) =>
    post<ResolveResult>("/api/workflow/resolve", { notice_id: noticeId, answers }),
  refusal: (id: string) => get<ResolveResult>(`/api/notices/${id}/refusal`),
  extractScrutiny: (file: File, signal?: AbortSignal) => {
    const body = new FormData();
    body.append("file", file);
    const url = "/api/scrutiny/extract";
    return request<ExtractionResult>(url, { method: "POST", body, signal });
  },
  confirmExtraction: (extractionId: string, fingerprint: string, confirmed: boolean, corrections: Record<string, string> = {}, signal?: AbortSignal) =>
    post<ExtractionConfirmationResult>("/api/scrutiny/confirm", { extraction_id: extractionId, fingerprint, confirmed, corrections }, signal),
  scrutinyRequests: (id: string, locale: Locale, extractionConfirmed = true, signal?: AbortSignal) =>
    get<ScrutinyRequestsResult>(`/api/scrutiny/${id}/requests?locale=${locale}&extraction_confirmed=${extractionConfirmed}`, signal),
  scrutinyQuestions: (id: string, locale: Locale, extractionConfirmed = true, signal?: AbortSignal) =>
    get<{ supported: boolean; questions: ScrutinyQuestion[] }>(`/api/scrutiny/${id}/questions?locale=${locale}&extraction_confirmed=${extractionConfirmed}`, signal),
  scrutinyQuestionPlan: (id: string, locale: Locale, extractionConfirmed = true, answers: Record<string, string> = {}, signal?: AbortSignal) =>
    answers && Object.keys(answers).length > 0
      ? post<MinimumQuestionPlanResult>("/api/scrutiny/question-plan", { notice_id: id, answers, extraction_confirmed: extractionConfirmed, locale }, signal)
      : get<MinimumQuestionPlanResult>(`/api/scrutiny/${id}/question-plan?locale=${locale}&extraction_confirmed=${extractionConfirmed}`, signal),
  resolveScrutiny: (noticeId: string, answers: Record<string, string>, extractionConfirmed = true, signal?: AbortSignal, documentStatuses: Record<string, EvidenceStatus> = {}) =>
    post<ScrutinyResolveResult>("/api/scrutiny/resolve", { notice_id: noticeId, answers, extraction_confirmed: extractionConfirmed, document_statuses: documentStatuses }, signal),
  resolveMinimumScrutiny: (noticeId: string, answers: Record<string, string>, extractionConfirmed = true, signal?: AbortSignal, documentStatuses: Record<string, EvidenceStatus> = {}) =>
    post<ScrutinyResolveResult>("/api/scrutiny/resolve-minimum", { notice_id: noticeId, answers, extraction_confirmed: extractionConfirmed, document_statuses: documentStatuses }, signal),
  evidence: (noticeId: string, statuses: Record<string, EvidenceStatus> = {}, signal?: AbortSignal) =>
    post<{ evidence: EvidenceRecommendation[]; missing_evidence: EvidenceRecommendation[] }>(`/api/scrutiny/${noticeId}/evidence`, { statuses }, signal),
  approveScrutiny: (noticeId: string, answers: Record<string, string>, draft: string, approved: boolean, documentStatuses: Record<string, EvidenceStatus> = {}, signal?: AbortSignal) =>
    post<{ status: string; handoff_allowed: boolean; message?: string; boundary?: string; missing?: string[]; safety_review?: ScrutinyResolveResult["safety_review"] }>(`/api/scrutiny/${noticeId}/review`, { answers, draft, approved, document_statuses: documentStatuses, extraction_confirmed: true }, signal),
  approveMinimumScrutiny: (noticeId: string, answers: Record<string, string>, draft: string, approved: boolean, documentStatuses: Record<string, EvidenceStatus> = {}, signal?: AbortSignal) =>
    post<{ status: string; handoff_allowed: boolean; message?: string; boundary?: string; missing?: string[]; safety_review?: ScrutinyResolveResult["safety_review"] }>(`/api/scrutiny/${noticeId}/review-minimum`, { notice_id: noticeId, answers, draft, approved, document_statuses: documentStatuses, extraction_confirmed: true }, signal),
};

// --- journey state ---

function read(key: string): string | null {
  return localStorage.getItem(key);
}

export const store = {
  locale(): Locale {
    return (read("taxmitra.locale") as Locale) || "en";
  },
  setLocale(locale: Locale) {
    localStorage.setItem("taxmitra.locale", locale);
  },
  citizenId(): string | null {
    return read("taxmitra.citizen");
  },
  setCitizenId(id: string | null) {
    if (id) localStorage.setItem("taxmitra.citizen", id);
    else localStorage.removeItem("taxmitra.citizen");
  },
  answers(noticeId: string): Record<string, string> {
    try {
      return JSON.parse(read(`taxmitra.answers.${noticeId}`) || "{}");
    } catch {
      return {};
    }
  },
  setAnswers(noticeId: string, answers: Record<string, string>) {
    localStorage.setItem(`taxmitra.answers.${noticeId}`, JSON.stringify(answers));
  },
  draft(noticeId: string): string | null {
    return read(`taxmitra.draft.${noticeId}`);
  },
  setDraft(noticeId: string, draft: string) {
    localStorage.setItem(`taxmitra.draft.${noticeId}`, draft);
  },
  scrutinyStage(noticeId: string): string {
    return read(`taxmitra.scrutiny.stage.${noticeId}`) || "requests";
  },
  setScrutinyStage(noticeId: string, stage: string) {
    localStorage.setItem(`taxmitra.scrutiny.stage.${noticeId}`, stage);
  },
  extractionConfirmed(noticeId: string): boolean {
    return read(`taxmitra.scrutiny.confirmed.${noticeId}`) === "true";
  },
  setExtractionConfirmed(noticeId: string, confirmed: boolean) {
    localStorage.setItem(`taxmitra.scrutiny.confirmed.${noticeId}`, String(confirmed));
  },
  uploadedNoticeId(): string | null {
    return read("taxmitra.scrutiny.uploadedNoticeId");
  },
  setUploadedNoticeId(noticeId: string) {
    localStorage.setItem("taxmitra.scrutiny.uploadedNoticeId", noticeId);
  },
  reset() {
    Object.keys(localStorage)
      .filter((k) => k.startsWith("taxmitra."))
      .forEach((k) => localStorage.removeItem(k));
  },
};

export function formatINR(amount: number): string {
  return `₹${amount.toLocaleString("en-IN")}`;
}

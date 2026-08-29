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
}

export interface Citation {
  id: string;
  section: string;
  title: string;
  source_name: string;
  official_url: string;
  accessed_date: string;
  verification: string;
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
}

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
  grounding: Grounding;
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
    status: "needs_confirmation" | "refused";
    confidence: number;
    warnings: string[];
    refusal_reason: string | null;
  };
  grounding: Grounding;
  extraction_id?: string;
  fingerprint?: string;
  requires_human_confirmation?: boolean;
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
  grounding?: { method: string; confidence: number; below_floor: boolean };
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
}
export interface ScrutinyResolveResult extends Omit<ResolveResult, "checklist" | "path"> {
  category: string;
  path?: { path_id: "ready_to_respond" | "needs_evidence" | "needs_review"; headline: Record<string, string>; professional_help_recommended: boolean };
  checklist?: ScrutinyChecklistItem[];
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

export const api = {
  citizens: () => get<Citizen[]>("/api/citizens"),
  notices: (citizenId: string) => get<NoticeCard[]>(`/api/notices?citizen_id=${citizenId}`),
  notice: (id: string) => get<NoticeCard>(`/api/notices/${id}`),
  explanation: (id: string, locale: Locale) =>
    get<Explanation>(`/api/ai/explanation/${id}?locale=${locale}`),
  questions: (id: string, locale: Locale) =>
    get<{ questions: Question[] }>(`/api/workflow/questions/${id}?locale=${locale}`),
  resolve: (noticeId: string, answers: Record<string, string>) =>
    post<ResolveResult>("/api/workflow/resolve", { notice_id: noticeId, answers }),
  refusal: (id: string) => get<ResolveResult>(`/api/notices/${id}/refusal`),
  extractScrutiny: (file: File, signal?: AbortSignal) => {
    const body = new FormData();
    body.append("file", file);
    const url = "/api/scrutiny/extract";
    return request<ExtractionResult>(url, { method: "POST", body, signal });
  },
  confirmExtraction: (extractionId: string, fingerprint: string, confirmed: boolean, signal?: AbortSignal) =>
    post<ExtractionConfirmationResult>("/api/scrutiny/confirm", { extraction_id: extractionId, fingerprint, confirmed }, signal),
  scrutinyRequests: (id: string, locale: Locale, extractionConfirmed = true, signal?: AbortSignal) =>
    get<ScrutinyRequestsResult>(`/api/scrutiny/${id}/requests?locale=${locale}&extraction_confirmed=${extractionConfirmed}`, signal),
  scrutinyQuestions: (id: string, locale: Locale, extractionConfirmed = true, signal?: AbortSignal) =>
    get<{ supported: boolean; questions: ScrutinyQuestion[] }>(`/api/scrutiny/${id}/questions?locale=${locale}&extraction_confirmed=${extractionConfirmed}`, signal),
  resolveScrutiny: (noticeId: string, answers: Record<string, string>, extractionConfirmed = true, signal?: AbortSignal) =>
    post<ScrutinyResolveResult>("/api/scrutiny/resolve", { notice_id: noticeId, answers, extraction_confirmed: extractionConfirmed }, signal),
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

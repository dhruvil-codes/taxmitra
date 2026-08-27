// API client + journey state persistence (localStorage).

export type Locale = "en" | "hi";

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

export function isScrutinyNotice(notice: Pick<NoticeCard, "category">): boolean {
  return notice.category === "scrutiny_142_1";
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

export interface ScrutinyRequest {
  request_id: string;
  original_text: string;
  what_department_is_asking: string;
  expected_evidence: string[];
  confidence: number;
  warnings: string[];
}

export interface ScrutinyRequestsResult {
  supported: boolean;
  notice_id: string;
  requests: ScrutinyRequest[];
  extraction: { source_type: string; requires_human_confirmation: boolean; confirmed: boolean };
  grounding?: { method: string; confidence: number; below_floor: boolean };
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

export interface ExtractionRequest {
  request_id: string;
  original_text: string;
  normalized_explanation: string;
  department_asks: string;
  expected_evidence: string[];
  classification_id: string;
  response_section: string;
  citations: Citation[];
  confidence: number;
  warnings: string[];
  grounding?: { method: string; confidence: number; below_floor: boolean };
}

export interface ExtractionResult {
  supported: boolean;
  extraction_id?: string;
  fingerprint?: string;
  requires_human_confirmation?: boolean;
  metadata?: {
    notice_reference?: string | null;
    section?: string | null;
    assessment_year?: string | null;
    response_deadline?: string | null;
  };
  requests?: ExtractionRequest[];
  extraction: {
    status: "needs_confirmation" | "refused";
    confidence: number;
    warnings: string[];
    refusal_reason?: string | null;
  };
  grounding: { method: string; confidence: number; below_floor: boolean };
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

export function isIntegrationError(error: unknown): boolean {
  return error instanceof TypeError || (error instanceof ApiError && [405, 502, 503, 504].includes(error.status));
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

async function get<T>(url: string): Promise<T> {
  const res = await fetch(apiUrl(url));
  if (!res.ok) throw new ApiError(url, res.status, await readError(res));
  return res.json();
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(apiUrl(url), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new ApiError(url, res.status, await readError(res));
  return res.json();
}

async function readError(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return await res.text();
  }
}

async function extractPdf(file: File): Promise<ExtractionResult> {
  const form = new FormData();
  form.append("file", file, file.name);
  // Do not set Content-Type here: the browser adds multipart/form-data and its boundary.
  const url = apiUrl("/api/scrutiny/extract");
  if (import.meta.env.DEV) {
    console.log("Extraction request:", {
      url,
      method: "POST",
      file: file.name,
      size: file.size,
      type: file.type,
      apiBase,
    });
  }
  const res = await fetch(url, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const errorDetail = await readError(res);
    if (import.meta.env.DEV) {
      console.error("Extraction failed:", {
        url,
        status: res.status,
        detail: errorDetail,
      });
    }
    throw new ApiError("/api/scrutiny/extract", res.status, errorDetail);
  }
  return res.json();
}

export const api = {
  citizens: () => get<Citizen[]>("/api/citizens"),
  notices: (citizenId?: string) => get<NoticeCard[]>(citizenId ? `/api/notices?citizen_id=${citizenId}` : "/api/notices"),
  notice: (id: string) => get<NoticeCard>(`/api/notices/${id}`),
  explanation: (id: string, locale: Locale) =>
    get<Explanation>(`/api/ai/explanation/${id}?locale=${locale}`),
  questions: (id: string, locale: Locale) =>
    get<{ questions: Question[] }>(`/api/workflow/questions/${id}?locale=${locale}`),
  resolve: (noticeId: string, answers: Record<string, string>) =>
    post<ResolveResult>("/api/workflow/resolve", { notice_id: noticeId, answers }),
  scrutinyRequests: (id: string, locale: Locale) => get<ScrutinyRequestsResult>(`/api/scrutiny/${id}/requests?locale=${locale}`),
  scrutinyQuestions: (id: string, locale: Locale) => get<{ questions: Question[] }>(`/api/scrutiny/${id}/questions?locale=${locale}`),
  scrutinyResolve: (noticeId: string, answers: Record<string, string>) => post<ResolveResult>("/api/scrutiny/resolve", { notice_id: noticeId, answers }),
  confirmExtraction: (extractionId: string, fingerprint: string) => post<{ supported: boolean; notice_id: string }>("/api/scrutiny/confirm", { extraction_id: extractionId, fingerprint, confirmed: true }),
  refusal: (id: string) => get<ResolveResult>(`/api/notices/${id}/refusal`),
  extractPdf,
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
  reset() {
    Object.keys(localStorage)
      .filter((k) => k.startsWith("taxmitra."))
      .forEach((k) => localStorage.removeItem(k));
  },
};

export function formatINR(amount: number): string {
  return `₹${amount.toLocaleString("en-IN")}`;
}

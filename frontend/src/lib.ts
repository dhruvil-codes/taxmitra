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

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
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

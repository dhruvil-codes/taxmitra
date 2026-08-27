# Tax Mitra — Frontend Contract

Everything you need to build the frontend without reading backend code:
the exact user input flow, every endpoint with real request/response shapes,
the i18n rules, DEMO_MODE behavior, and error handling.

Backend is **frozen on this contract** — additive changes only. If something
here doesn't match what the API returns, that's a backend bug; file it, don't
code around it.

---

## 1. The user input flow — what a citizen actually gives Tax Mitra

**PDF upload is supported for ordinary text-based Section 142(1) notices. OCR is not supported in V1.**

| # | Screen | What the user gives | Tap cost |
|---|--------|--------------------|----------|
| 1 | Landing / anywhere | Language: English or हिंदी | 1 tap |
| 2 | Login | Pick a demo citizen (mock, labeled "fictional data"). No signup, no PAN entry, no OTP. | 1 tap |
| 3 | Dashboard | Nothing. Their notice is already there (pre-loaded demo data). | 0 |
| 4 | Understand | Nothing. Read the plain-language explanation; optionally tap citation chips to open the Source Panel. | 0 |
| 5 | Questions | 3 questions × one tap each: **Yes / No / Not sure**. "Not sure" is a first-class answer — it changes the checklist. | 3 taps |
| 6 | Checklist → Draft | Nothing required. Draft is pre-filled by the rules engine; editing is optional. | 0 |
| 7 | Final action | Copy draft → "Continue on the official e-Filing portal ↗". Tax Mitra submits nothing. | 1–2 taps |

**Landing-page copy angle:** "No forms to fill. Answer 3 questions in your
language — we handle the rest."

**V1 PDF scope:** notice PDFs vary wildly in
layout; a misparse means wrong guidance, which is our worst failure mode.
The prototype uses pre-loaded demo notices and says so. "Drop your notice
PDF" with OCR → DIN extraction → auto-classify is on the post-hackathon
roadmap, always with a human confirm step before anything is believed.

---

## 2. Conventions

- **Base URL:** same origin (`/api/...`). In dev, Vite proxy `/api` → `http://127.0.0.1:8000`.
- **Locale:** `en` or `hi`, passed as `?locale=`. Anything else → **422**.
- **Bilingual fields** are objects: `{"en": "...", "hi": "..."}` — pick `field[locale] ?? field.en`.
- **Amounts:** raw numbers (INR). Format with `₹${n.toLocaleString("en-IN")}` → `₹45,000`.
- **Dates:** ISO `YYYY-MM-DD`. `days_remaining` is an integer (or `null` when no deadline applies).
- **Status values:** `"action_required"` | `"due_soon"` | `"expired"` | `"no_deadline"`.
- All responses are JSON. GZip is on; security headers are on. Rate limit: `/api/ai/*` is **10 req/min/IP** → 429 when exceeded.

---

## 3. Endpoints

### 3.1 `GET /api/health`
Deployment dashboard. No auth.

```json
{
  "status": "ok",
  "version": "0.2.0",
  "demo_mode": true,
  "live_ai_allowed": false,
  "kb_loaded": false,
  "chat_model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-small",
  "retrieval_method": "lexical",
  "static_fallbacks": 2,
  "static_integrity": "ok"
}
```

### 3.2 `GET /api/citizens` → `Citizen[]`
For the mock login screen (show `name`, `city`, `profile_note[locale]`).

```json
[{
  "id": "C-001",
  "name": "Aarav Sharma",
  "pan_masked": "ABCD••••E1F (fictional)",
  "city": "Pune",
  "preferred_locale": "en",
  "profile_note": { "en": "Salaried teacher...", "hi": "वेतनभोगी शिक्षक..." }
}]
```

### 3.3 `GET /api/notices?citizen_id=C-001` → `NoticeCard[]`
`citizen_id` optional (no filter = all notices). Dashboard cards.

```json
[{
  "id": "N-2026-001",
  "section": "143(1)(a)",
  "category": "income_mismatch_143_1a",
  "supported": true,
  "title": { "en": "Income mismatch — adjustment proposed", "hi": "आय बेमेल — संशोधन का प्रस्ताव" },
  "amount_in_question": 45000,
  "issue_date": "2026-08-13",
  "assessment_year": "2025-26",
  "due_date": "2026-09-12",
  "days_remaining": 18,
  "status": "action_required"
}]
```

- `supported: true` → "Start" CTA into the journey.
- `supported: false` → refusal screen (see 3.7).

### 3.4 `GET /api/notices/{id}` → `NoticeCard` + extras
Adds `official_text` (the intimidating letter — show collapsible), `income_source` (**bilingual `{en, hi}`**), `official_reference` (DIN), `citizen_id`. **404** if unknown.

### 3.5 `GET /api/ai/explanation/{notice_id}?locale=hi` → `Explanation`
The Understand screen. Server-rendered text (placeholders already filled — never string-replace on the client).

```json
{
  "content": {
    "plain_language": "आयकर विभाग ने आपके मूल्यांकन वर्ष 2025-26 के रिटर्न की तुलना...",
    "what_this_does_not_mean": "इसका यह मतलब नहीं कि आप पर तुरंत ₹45,000 का कर बनता है...",
    "possible_reasons": ["यह आय प्राप्त तो हुई थी, पर...", "...", "...", "...", "..."]
  },
  "citations": [{
    "id": "kb-143-1-overview",
    "section": "143(1)",
    "title": "...",
    "source_name": "Income Tax Act, 1961 — India Code",
    "official_url": "https://...",
    "accessed_date": "2026-08-24",
    "verification": "pending",
    "excerpt": "..."
  }],
  "scope_statement": { "en": "Covers only the listed notice types...", "hi": "केवल सूचीबद्ध नोटिस प्रकारों..." },
  "source": "static",
  "degraded": false,
  "demo_mode": true,
  "grounding": { "method": "lexical", "confidence": 0.349, "below_floor": false }
}
```

UI rules:
- **SavedGuidanceBadge** (`✓ Using verified saved guidance`): show when `source !== "live"`.
- **Citation chips** → open the **in-app Source Panel** using the citation fields (never link out as the only evidence — the panel is the evidence, the URL is a bonus button).
- Show `scope_statement[locale]` on the same screen.
- Errors: **400** unsupported notice (go to refusal), **404** unknown, **422** bad locale, **429** rate-limited, **503** AI unavailable and no saved content (show retry).

### 3.6 `GET /api/workflow/questions/{notice_id}?locale=en` → `{questions: Question[]}`

```json
{ "questions": [
  { "id": "q1_received", "text": "Did you receive interest income of ₹45,000 ...?", "help": "Check your bank statement...", "options": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}, {"id": "unsure", "label": "Not sure"}] },
  { "id": "q2_in_return", "...": "..." },
  { "id": "q3_documents", "...": "..." }
]}
```

Render one question at a time; option ids are exactly `yes | no | unsure`.

### 3.7 `POST /api/workflow/resolve`
Body: `{"notice_id": "N-2026-001", "answers": {"q1_received": "yes", "q2_in_return": "no", "q3_documents": "unsure"}}`

**Supported → everything the last three screens need, in one response:**

```json
{
  "supported": true,
  "path": { "path_id": "agree_report_now", "position": "agree", "headline": {"en": "...", "hi": "..."}, "guidance": {"en": "...", "hi": "..."} },
  "checklist": [{ "id": "doc_ais_download", "title": {"en": "...", "hi": "..."}, "why_needed": {"en": "...", "hi": "..."} }],
  "deadline": { "due_date": "2026-09-12", "days_remaining": 18, "status": "action_required" },
  "draft": "Subject: Response to intimation under section 143(1)(a) - DIN-DEMO-...",
  "official_step": {
    "label": {"en": "Submit your response on the official e-Filing portal", "hi": "आधिकारिक e-Filing पोर्टल पर अपना उत्तर जमा करें"},
    "url": "https://www.incometax.gov.in/iec/foservices/",
    "boundary": {"en": "Tax Mitra has not submitted your response...", "hi": "Tax Mitra ने आपका उत्तर जमा नहीं किया है..."}
  }
}
```

**The final-action screen must always show** `official_step.boundary[locale]` (amber), the deadline block, the condensed checklist, and a copyable draft.

**Unsupported notice → refusal payload (HTTP 200):**

```json
{
  "supported": false,
  "headline": {"en": "We can't safely guide you through this yet", "hi": "..."},
  "why": {"en": "...", "hi": "..."},
  "suggestion": {"en": "...", "hi": "..."},
  "official_links": [{ "label": {"en": "...", "hi": "..."}, "url": "https://www.incometax.gov.in/..." }]
}
```

Errors: **404** unknown notice, **422** missing/invalid/non-string answers.

### 3.8 `GET /api/notices/{notice_id}/refusal` → refusal payload
Same shape as above. **400** if the notice *is* supported.

---

### 3.9 POST /api/scrutiny/extract - PDF extraction

Send multipart form data with field `file` and content type `application/pdf`.
Files are limited to 10 MB. V1 supports ordinary text PDFs only; OCR is not
supported. Uploaded bytes are processed in memory and are never persisted or
logged.

Success returns `supported: true`, `extraction.status: "needs_confirmation"`,
an ephemeral `extraction_id`, a server-generated `fingerprint`, notice
metadata, and requests containing `request_id`, `original_text`,
`classification_id`, `response_section`, `citations`, `confidence`,
`warnings`, and per-request `grounding` metadata. Top-level `grounding` has
`method`, `confidence`, and `below_floor`.

Malformed, empty, scanned/image-only, unrelated, unsupported, unclassifiable,
or below-grounding-floor PDFs return `supported: false` and
`extraction.status: "refused"` with a machine-readable `refusal_reason`.

### 3.10 POST /api/scrutiny/confirm

After reviewing the extraction, send
`{"extraction_id":"...", "fingerprint":"...", "confirmed":true}`.
The fingerprint is checked against an ephemeral in-memory session, so arbitrary
client-created requests are not trusted. The response returns `notice_id`
equal to the opaque extraction id. Use it with the existing scrutiny requests,
questions, and resolve endpoints. Before confirmation those endpoints refuse;
no questions, checklist, or draft can be generated. Sessions expire after 30
minutes and contain no PDF bytes.

The enforced flow is: PDF extraction -> human confirmation -> deterministic
rules/questions -> checklist/draft. Tax Mitra never submits anything.

## 4. Journey state (localStorage)

The backend is stateless; the frontend owns journey persistence. Keys used by the current frontend (keep the same names so a returning demo resumes):

| Key | Value |
|-----|-------|
| `taxmitra.locale` | `"en" \| "hi"` |
| `taxmitra.citizen` | citizen id (`"C-001"`) |
| `taxmitra.answers.{noticeId}` | JSON `{"q1_received": "yes", ...}` |
| `taxmitra.draft.{noticeId}` | edited draft text |

---

## 5. DEMO_MODE semantics (the trust story)

- `demo_mode: true` → the AI explanation **never** calls OpenAI; it serves verified static content. This is the designed path, not an error.
- `source`: `"static"` (file, committed to repo) → `"cache"` (in-memory, from a live run) → `"live"` (fresh OpenAI call — dev-time only).
- `degraded: true` only when stale cache is served because live AI is off.
- `grounding.method`: `"lexical"` or `"embedding"` — how the answer was anchored to the corpus. Both enforce the confidence floor; `below_floor: true` means "refuse rather than guess" (you will not see it on the hero journey).

---

## 6. Error-handling matrix

| Status | When | UI |
|--------|------|----|
| 400 | Explanation/refusal requested for an unsupported/supported mismatch | Route to the correct screen |
| 404 | Unknown notice/citizen id | "Not found" + back to dashboard |
| 422 | Bad locale, missing answers, non-string answers | Show which field, keep user in place |
| 429 | >10 AI calls/min | "Please wait a moment" |
| 503 | No saved content and live AI unavailable | Retry button (should never happen in DEMO_MODE) |

---

## 7. Connection checklist

1. Vite dev proxy: `server.proxy['/api'] → http://127.0.0.1:8000`.
2. Run backend: `cd backend && DEMO_MODE=true python -m uvicorn app.main:app --reload`.
3. Verify with `GET /api/health` → `"status": "ok"`.
4. Build the 6 screens against §3; keep bilingual pickers `field[locale] ?? field.en`.
5. Prod: `npm run build` → FastAPI serves `frontend/dist/` at the root (single service, no CORS).

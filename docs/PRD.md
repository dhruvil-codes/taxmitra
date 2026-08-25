# Tax Mitra — Product Requirements Document (PRD)

**Version:** 1.0 · **Date:** 2026-08-24 · **Deadline: Aug 28, 2026, 8:00 PM IST (no grace period)**

> **Purpose of this document.** This is the single source of truth for building Tax Mitra for the Build What Moves India hackathon. It contains the product definition, scope ladder, technical specification, schedule, and — critically — the **current implementation status** so work can resume in a fresh session without losing context. Read top to bottom once; then work from §16 (status) and §15 (schedule).

---

## 1. Product overview

**Tax Mitra 🇮🇳 — Your tax notice, made understandable.**

A guided digital experience that turns a confusing Indian income tax notice into: a plain-language explanation (in the citizen's language, cited to official sources), a personalized document checklist, an editable response draft, and a clear next official step.

**Journey:** Notice → Understand → Answer → Prepare → Review → Act

**Philosophy:** **AI explains. Rules decide. Humans approve.**

**What it is NOT:** a chatbot, a tax filing app, a CA replacement, or a government site redesign. It is a guided response layer between a confusing notice and a citizen's next action. Tax Mitra never submits anything — the official e-Filing portal remains the only authoritative channel.

**Key product statement:** *"We're not using AI to answer a taxpayer's questions. We're using AI to remove the need for the taxpayer to know what questions to ask."*

---

## 2. Hackathon context (constraints that shape everything)

| Fact | Detail |
|---|---|
| Event | Build What Moves India (Varun Mayya × OpenAI) — "rethink public service websites" |
| Deadline | **Aug 28, 2026, 8:00 PM IST**. Submit by 6 PM for a 2-hour buffer |
| Requirement | Prototype must be **built with Codex / meaningfully AI-assisted** and/or **powered by an OpenAI model**. Our OpenAI API layer satisfies "powered by"; Codex evidence is documented separately (§14) |
| Submission | Live public link (opens in browser, no access request) · video ≤ 2 min (minute 1 = citizen demo, minute 2 = how/why built) · project summary < 250 words · mock credentials if login |
| Judging criteria | Problem · Working build · Usability · Product thinking · End-to-end thinking · **Honesty** (disclose mocks/limitations) |
| Two-stage | Top 250 (Aug 28–Sep 1) → mentorship week → resubmit Sep 7 → top 10 → live finals Bengaluru Sep 12 |
| Team | Solo (Dhruvil), building with an AI coding agent |
| Repo | https://github.com/dhruvil-codes/taxmitra (branch `main`, pushed) |

---

## 3. Scope ladder (build in this order — never below reliability)

**P0 — Release Candidate (must be flawless):**
1. English + हिंदी (two languages done well)
2. ONE synthetic 143(1)(a) income-mismatch notice, one complete rules path
3. Full journey: Notice → Understand → Answer → Prepare → Review → Act
4. Citations with full provenance + in-app Source Panel
5. Unsupported-notice refusal behavior (honesty screen)
6. Final-action screen with "Tax Mitra has not submitted your response" boundary
7. Mobile usability (360px), clear disclosure everywhere
8. Deployed public URL on Railway

**P1 — only after a stranger completes RC unaided:** one more vetted language (தமிழ் or বাংলা or తెలుగు or मराठी) · 139(9) defective-return second path.

**P2 — Sep 7 resubmission stretch:** voice TTS · more languages · PDF export of response · broader corpus.

**Removed for stability:** Groq fallback (OpenAI-only, single provider) · voice in RC · 10 languages in RC.

**Hard cut order if behind:** unvetted languages → 139(9) → never cut the hero journey, refusal screen, or citations.

---

## 4. Screen-by-screen requirements

All screens carry the **DisclaimerBanner**: "Independent prototype. All data is fictional and synthetic." Plus the **LanguageSelector** (EN/हिं) and **SavedGuidanceBadge** ("✓ Using verified saved guidance") whenever static content is served — degradation is always visible, never silent.

1. **Landing** — Hero: "Got a confusing income tax notice? 😰" → value line → CTA straight into demo. The four answers above the fold: *What happened? · Why did I get it? · What do I need? · What do I do next?* Then the "Why not just ask ChatGPT?" strip (§6). Then trust strip.
2. **Login (mock)** — Pick the demo citizen. Labeled "Demo login", mock credentials visible (hackathon rule).
3. **Dashboard** — Notice cards: type, amount involved, "Respond by" + days-remaining chip, status (Action required / Due soon). Plain labels only.
4. **Understand** — Official wording ↔ plain-language explanation side-by-side (collapsible official text), "What this does NOT mean" callout (critical: amount ≠ automatic liability), **CitationChips** opening the **Source Panel**, possible-reasons list.
5. **Answer (guided questions)** — 3 questions, options Yes / No / I'm not sure, with help text. No blank text box.
6. **Prepare (checklist)** — Personalized documents, each with "Why do I need this?" First item becomes "obtain evidence" when the user lacks documents.
7. **Draft** — Rules-built response letter, fully editable; position headline ("You disagree: this income is already in your return"); user can Edit / Accept. Drafts are in English (stated product decision — official responses are typically English).
8. **Review** — Summary card: issue, amount, position, documents count, deadline.
9. **Final Action (the payoff — best screen in the product)** — What to do ("Submit your response on the official e-Filing portal") · by when (deadline + days chip) · what you need (condensed checklist) · where (**"Continue on the official Income Tax e-Filing portal ↗"** button → https://www.incometax.gov.in/iec/foservices/) · always-visible boundary: **"Tax Mitra has not submitted your response. Nothing has been sent to the Income Tax Department."** Draft copyable.
10. **Unsupported / Refusal** — "We can't safely guide you through this yet" + why + official links + professional-help suggestion. Reached from the s.148 demo notice.

**Copy rules:** stepper = the four questions; every screen heading answers one of them; tap-to-explain on legal terms; "Amount involved / Respond by / Action required" — never "pursuant/aforementioned".

---

## 5. Rules engine specification (pure Python, zero AI)

Located in `backend/app/rules/`. Deterministic: same inputs → same outputs. Locked by pytest.

### 5.1 Classification (`notice_types.py`)
- `classify_notice(notice)` maps structured metadata → `NoticeCategory`: section starting `143(1)` → `INCOME_MISMATCH_143_1A`; `139(9)` → `DEFECTIVE_RETURN_139_9` (recognized, not yet supported); anything else → `UNSUPPORTED`.
- `SUPPORTED_CATEGORIES = {INCOME_MISMATCH_143_1A}` for RC.

### 5.2 Deadlines (`deadlines.py`)
- `RESPONSE_WINDOWS_DAYS = {INCOME_MISMATCH_143_1A: 30}` (TODO-VERIFY Day 3 vs official source).
- `compute_due_date(issue_date, category)`, `days_remaining(due, today=None)`, `deadline_status(due, today)` → `action_required` (>7 days) | `due_soon` (≤7) | `expired` (<0). `today` injectable for tests.

### 5.3 Guided questions (`decision_trees.py`)
- 3 questions, bilingual (en/hi), placeholders `{amount}`, `{assessment_year}` rendered from notice data:
  - `q1_received` — "Did you receive this {amount}?"
  - `q2_in_return` — "Was this income already included in your tax return?"
  - `q3_documents` — "Do you have a document that supports your answer?"
- Options: yes / no / unsure.

### 5.4 Response paths (`response_paths.py`) — the decision table

Base path keyed by (q1, q2); q1 dominates:

| q1 | q2 | path_id | position |
|---|---|---|---|
| no | any | `disagree_not_received` | disagree |
| unsure | any | `not_sure_verify_payer` | not_sure |
| yes | yes | `disagree_already_reported` | disagree |
| yes | no | `agree_report_now` | agree |
| yes | unsure | `not_sure_check_return` | not_sure |

**Evidence overlay:** q3 = yes → `evidence: available`; no → `missing`; unsure → `unsure`. When not `available`, `doc_ais_download` is inserted as the first checklist item, and the draft's documents-sentence changes accordingly.

Each path carries bilingual `headline` + `guidance` + `checklist_ids` + `draft_template_id`. `resolve_path()` is total over all 27 answer combinations.

### 5.5 Checklists (`checklists.py`)
Documents (bilingual, each with `why_needed`): `doc_26as` (Form 26AS/AIS statement) · `doc_itr_extract` (filed return pages) · `doc_bank_statement` · `doc_interest_certificate` (Form 16A) · `doc_computation` · `doc_ais_download` (how-to, appears when evidence missing) · `doc_payer_confirmation`. Unknown ids raise (checklists must never silently shrink).

### 5.6 Refusal (`refusal.py`)
`build_refusal(category)` → bilingual headline/why/suggestion + official links (e-Filing portal, help centre). Deterministic.

### 5.7 Draft builder
`build_draft(template, notice, citizen, answers, due_date)` fills slots `{citizen_name} {pan_masked} {section} {din} {assessment_year} {amount} {income_source} {issue_date} {deadline_date} {documents_sentence} {today_date}` in templates from `data/draft_templates.json`. **The rules engine produces the complete draft; AI polish is optional and only on cache miss.**

---

## 6. Messaging + the "why not just ChatGPT?" defense

**Frame (everywhere):** *"You got a tax notice. Here's what happened, why, what you need, and what to do next."*

**Defense kit** (deployed on: landing strip, video beat, README table, finals Q&A card):
1. **Blank-box problem** — ChatGPT needs you to know what to ask; questions here come from a deterministic decision tree. *"We use AI to remove the need to know what questions to ask."*
2. **Answer ≠ journey** — Tax Mitra carries state: classification, rules-computed deadline, answer-derived checklist, structured draft, forced review, routing to the exact official step.
3. **Grounded + cited vs. from memory** — explanations come only from retrieved official-source context with citations; refuses when grounding is weak; a chatbox always answers.
4. **Determinism** — same notice + answers = same path, every time; pytest suite in repo; deadlines computed by rules, never a model.
5. **Built for the real user** — mobile-only, regional-language users can't prompt; they can tap Yes/No/Not sure in their language.
6. **Killer line** — *"ChatGPT is a brilliant engine. A citizen with a notice needs a road from notice to response. Tax Mitra is that road."*

---

## 7. Knowledge base & RAG specification

**Why RAG, not fine-tuning:** fine-tuning can't cite, is slow/costly; RAG gives grounding + citations + a confidence gate, fully OpenAI-powered.

**Corpus format** — markdown files in `backend/app/knowledge/corpus/` with frontmatter:
```
---
id: kb-143-1a-mismatch
section: "Section 143(1)(a), Income-tax Act, 1961"
title: "..."
source_name: "India Code — Income-tax Act, 1961"
official_url: https://www.indiacode.in/linkin/gl/act1961/
accessed_date: 2026-08-24
verification: pending        # flipped to "verified" only after manual Day-3 check
tags: 143(1)(a), mismatch
---
Body text...
```

**Corpus inventory (RC ~12 chunks):** ✅ written: `kb-143-1-overview`, `kb-143-1a-mismatch`, `kb-285ba-information-sources`, `kb-ecampaign-response`, `kb-response-window-30d`, `kb-procedure-disagree-already-reported`. ⬜ to write: `kb-procedure-agree-missed-income`, `kb-procedure-not-received`, `kb-professional-help` (when to consult a CA), `kb-glossary-intimation`, `kb-glossary-assessment-year`, `kb-139-9-defective` (P1 stub).

**⚠️ Important provenance note:** automated fetch of `.gov.in` pages is blocked (bots refused — verified during Day 0). Corpus bodies are currently accurate *summaries* marked `verification: pending`. **Day-3 protocol:** manually open each `official_url`, verify the chunk's claims, replace/annotate with verbatim excerpts where possible, flip to `verification: verified`, and record it in `docs/legal_verification_checklist.md`. The user can manually download official pages/PDFs and drop them into the corpus folder for exact quoting.

**Pipeline:** `scripts/build_kb.py` → parse frontmatter+body → embed bodies (model from `OPENAI_EMBEDDING_MODEL`, default `text-embedding-3-small`) → write `app/knowledge/vectors.json` (id, vector, metadata) — loaded in-memory at runtime (README notes pgvector/Qdrant for the 1M-user story). **Retriever:** cosine top-k (k=4), confidence = top score; `retrieval_confidence_floor = 0.30` — below floor → refusal path, never a guess.

**Citation UX:** explanations end with CitationChips → **in-app Source Panel** (stable, instant, offline): source title, section, excerpt, `official_url`, accessed date, verification status. External "View at source ↗" is secondary — the demo never depends on a government page loading. Scope statement on explanation screens: "Covers only the listed notice types; the official portal remains authoritative."

---

## 8. AI layer specification (OpenAI-only, config-driven)

**Hard rule: model names are NEVER hardcoded at call sites.** All in `backend/app/config.py`, overridable via env: `OPENAI_CHAT_MODEL` (default `gpt-4o-mini`), `OPENAI_EMBEDDING_MODEL` (default `text-embedding-3-small`), `OPENAI_API_KEY`, `DEMO_MODE` (bool), `AI_RATE_LIMIT` (default "10/minute").

**Serving chain (cache.py):** static_fallbacks JSON → in-memory cache → live OpenAI call (skipped entirely when `DEMO_MODE=true`). Response includes `source: "static" | "cache" | "live"` and `degraded` flag → drives SavedGuidanceBadge.

**Budget strategy (account balance ≈ $2–3):** all spend is dev-time pre-generation (~8 explanation calls + ~27 draft polishes ≈ **< $0.50 total**); judging costs **$0** because DEMO_MODE serves static only. Rate-limit live routes anyway.

**Prompts (prompts.py):** structured JSON outputs; explain/translate grounded strictly in retrieved context — "answer ONLY from the provided context; cite the provided source ids; if the context does not support an answer, say so."

**Static fallback files:** `backend/app/static_fallbacks/explanation_income_mismatch_143_1a_en.json` and `_hi.json` — hand-written quality content with slots `{amount} {assessment_year} {income_source}`, `possible_reasons[]`, `what_this_does_not_mean`, `citations: [chunk_ids]`. ⬜ Still to write.

---

## 9. API specification (FastAPI)

| Endpoint | Method | Returns |
|---|---|---|
| `/api/health` | GET | `{status, demo_mode, kb_loaded, version}` |
| `/api/citizens` | GET | list of demo citizens |
| `/api/notices?citizen_id=` | GET | notice cards + computed `due_date`, `days_remaining`, `status` |
| `/api/notices/{id}` | GET | full notice + `category` + `supported` |
| `/api/notices/{id}/questions?locale=en\|hi` | GET | questions with options + help, placeholders rendered |
| `/api/notices/{id}/explanation?locale=` | GET | `{content{plain_language, what_this_does_not_mean, possible_reasons[]}, citations[], source, degraded}` |
| `/api/workflow/resolve` | POST | body `{notice_id, answers{q1_received,q2_in_return,q3_documents}}` → if supported: `{path{path_id,position,headline,guidance}, checklist[], deadline, draft}`; else refusal payload (§4.10) |

FastAPI serves the built frontend (`frontend/dist`) at `/` — one service, one public link, no CORS. Dev: Vite :5173 proxies `/api` → uvicorn :8000.

---

## 10. Data models (synthetic, fictional)

- **Citizen** `C-001` Aarav Sharma, Pune, masked fictional PAN — done.
- **Notice `N-2026-001`** (hero): 143(1)(a) income mismatch, ₹45,000 interest income "Demo Bharat Bank (fictional)", issue 2026-08-13, AY 2025-26, fictional DIN, full realistic official_text — done.
- **Notice `N-2026-002`** (refusal demo): s.148 reassessment, AY 2021-22, ₹1,20,000 — done.
- **Draft templates** — 5 templates (one per path) with slots — done (`data/draft_templates.json`).

---

## 11. Architecture & repo structure

```
tax-mitra/  (github.com/dhruvil-codes/taxmitra, branch main)
├── backend/
│   ├── app/
│   │   ├── config.py            ✅ done (env-driven, no hardcoded models)
│   │   ├── main.py              ⬜ TODO
│   │   ├── routers/{notices,workflow,ai}.py  ⬜ TODO
│   │   ├── rules/               ✅ done (all 6 modules)
│   │   ├── knowledge/           ✅ corpus×6/12 · ⬜ loader/embedder/retriever
│   │   ├── ai/{provider,cache,prompts}.py   ⬜ TODO
│   │   ├── data/                ✅ done (citizens, notices, draft_templates)
│   │   └── static_fallbacks/    ⬜ TODO (EN/HI explanations)
│   ├── scripts/{build_kb.py, pregenerate.py} ⬜ TODO
│   ├── tests/                   ⬜ TODO (pytest — the Codex-evidence module)
│   └── requirements.txt         ✅ done (fastapi, uvicorn, pydantic-settings, openai, numpy, slowapi, httpx, pytest)
├── frontend/                    ⬜ TODO (React 18 + TS + Vite + Tailwind v4, react-router-dom)
│   └── src/{pages×10, components×9, locales{en,hi}, lib}
├── docs/PRD.md                  ✅ this file
├── BUILD_LOG.md                 ⬜ TODO (start immediately — see §14)
└── README.md                    ✅ skeleton (expand Day 4)
```

**Deployment:** single Railway service (no cold-sleep; env vars: OPENAI_API_KEY, DEMO_MODE=true from Day 3). Backup: Render free + cron-job.org 10-min pings. Commit `frontend/dist` on deploy days (gitignore excludes it normally — force-add for deploys, or build in CI later).

---

## 12. Non-functional requirements

Mobile-first 360px · large type, strong contrast · keyboard navigation · screen-reader labels (aria) · no color-only information · low-bandwidth friendly (system Indic fonts + Noto fallback, no heavy assets, Lighthouse check) · server-side keys only (never in frontend) · localStorage journey resume (keys: `taxmitra.locale`, `taxmitra.citizen`, `taxmitra.journey.{notice_id}` = `{step, answers, draft_edits}`) · no real PAN/Aadhaar/OTP anywhere.

---

## 13. Compliance & honesty checklist (non-negotiable)

- [ ] No government emblems/logos; never imply official status
- [ ] Banner on every page: "Independent prototype. All data is fictional and synthetic."
- [ ] Mock login labeled; mock credentials visible on the login screen
- [ ] README honesty table — Real: rules engine, workflow, RAG+citations, EN/HI localization, caching, DEMO_MODE. Mocked: notices, citizens, documents, login, e-filing link-out. Deferred: voice
- [ ] KB sources listed with official URLs + accessed dates + verification status
- [ ] In-product scope statement (only listed notice types; portal authoritative)
- [ ] "How AI contributed to the build" README section backed by BUILD_LOG

---

## 14. AI-contribution evidence (Codex requirement)

- `BUILD_LOG.md` at repo root, **timestamped entries from Day 0**, three categories per entry: **AI-generated / human-reviewed / human-changed-or-rejected** (+ why).
- Include ≥1 substantial named example for README + 250-word summary (e.g., "rules-engine pytest suite produced with AI assistance, manually validated against the Income-tax Act; corrections listed in BUILD_LOG").
- Do not lean on "powered by an OpenAI model" as the headline evidence — it's a supporting line.

---

## 15. Build schedule (IST) & validation gates

**Day 0 — Mon Aug 24:** ✅ repo + skeleton pushed (commit `bc84bc8`) · ✅ rules engine + synthetic data written · ⬜ BUILD_LOG · ⬜ pytest run (Python env needed) · ⬜ hello-world Railway deploy + env vars.
**Day 1 — Tue Aug 25:** remaining corpus · loader/embedder/retriever + tests · routers + main + `/api/health` · pytest suite green · static fallbacks EN/HI · frontend scaffold + Landing + Login + Dashboard + Understand (with SourcePanel). *Gate: deployed — a stranger can open the notice and read a cited explanation in EN/हिं.*
**Day 2 — Wed Aug 26:** full journey screens (Questions → Checklist → Draft → Review → FinalAction) · localStorage resume · SavedGuidanceBadge · **kill-the-key drill** (DEMO_MODE/invalid key → journey completes with badge). *Gate: E2E on phone.*
**Day 3 — Thu Aug 27:** refusal screen wired · **manual legal verification pass** (flip corpus to verified + checklist doc) · **stranger test** (link to 1–2 people who haven't seen the plan; no explanation; watch for: amount, deadline, documents needed, final action; fix top 3 hesitations) · demo-condition citation test (deployed URL, phone, throttled network, fresh session) · enable DEMO_MODE on prod · QA sweep · lock video script + 2 rehearsals.
**Day 4 — Fri Aug 28:** **10 AM hard freeze** → record video → 250-word summary → README final → **submit by 6 PM**.

---

## 16. Current implementation status (read this first when resuming)

> **UPDATE (Aug 25): Backend HARDENED and frozen on the API contract — 47/47 pytest, live E2E verified, pushed (`e8b25bd`). Frontend is being rebuilt by the human against `docs/FRONTEND_CONTRACT.md` (input flow, every endpoint, i18n rules, DEMO_MODE semantics, error matrix, localStorage keys). No OCR/PDF upload — deliberate scope decision, documented in the contract. Remaining: (1) user rebuilds frontend → reconnect (contract §7 checklist); (2) deploy to Railway (`OPENAI_API_KEY` + `DEMO_MODE=true`, verify `/api/health` shows `static_integrity: ok`); (3) Day-3 items in §15 (legal verification, stranger test, DEMO_MODE drill on prod, video).**
>
> **Hardening pass contents (Aug 25):** lexical grounding fallback (confidence floor enforceable with no vectors.json, no API key, and in DEMO_MODE — embeddings never touched); `grounding {method, confidence, below_floor}` on every explanation; GZip + security headers + request logging; SPA path-traversal containment; enriched `/api/health` with `static_integrity` self-check (regression guard for the Day-0 dropped-citation-id bug class); locale validated (422); bilingual `income_source` ({en, hi}) with locale-aware rendering — fixed raw-English-in-Hindi seam; +13 tests.

**Committed & pushed:** skeleton + README (`bc84bc8`), PRD (`1502176`), Day 0/1 build (`f168a98`), backend hardening pass (`e8b25bd`).

**Next steps, in order (next session starts here):**
1. Human rebuilds the frontend against `docs/FRONTEND_CONTRACT.md`; reconnect per contract §7 (Vite proxy → uvicorn :8000, verify `/api/health`).
2. Deploy to Railway (user): env `OPENAI_API_KEY` + `DEMO_MODE=true`; verify `/api/health` → `status: ok`, `static_integrity: ok`, `retrieval_method: lexical`.
3. Optional: run `python -m scripts.build_kb` + `pregenerate.py` with the real key (vectors.json + RAG-grounded fallbacks; hand-authored fallbacks already work — after this, health flips to `retrieval_method: embedding` outside DEMO_MODE).
4. Day-3 items in §15: manual legal verification (flip corpus `verification: pending → verified`), stranger test + top-3 fixes, demo-condition citation test, kill-the-key drill on prod, QA sweep.
5. Day-4: 10 AM freeze, video (§17), 250-word summary, README honesty tables, submit by 6 PM IST.

**Known issues / session notes:**
- `.gov.in` sites block automated fetches — corpus verification is a manual Day-3 task (user can download official pages/PDFs into the corpus folder for exact quoting).
- Model names: config/env only, never hardcoded (explicit user requirement).
- Drafts stay in English; UI + explanations localized (explicit product decision).
- Dev environment: Python 3.11.9 + Node 24 on Windows/Git Bash, deps installed globally (no venv in repo) — works as-is; Railway installs from `requirements.txt`.

---

## 17. Video script (2:00 — locked Day 3 night, rehearsed ×2)

- **0:00–0:20 Hook:** real 143(1)(a) text on screen. "If you received this, would you know what to do?"
- **0:20–0:55 Hero demo (one take):** demo citizen → dashboard → side-by-side + "what this does NOT mean" → tap citation → Source Panel → switch to हिंदी → 3 questions → checklist → edit draft → final-action screen + "Tax Mitra has not submitted your response."
- **0:55–1:15 Safety behaviors:** s.148 notice → refusal + official links → kill-the-key moment ("verified saved guidance" — journey completes without live AI).
- **1:15–1:45 How & why:** "AI explains (grounded + cited). Rules decide. Humans approve." · deterministic tested engine · KB from official sources · pre-generation ("instant, ~$0 to serve") · GPT defense in one breath.
- **1:45–2:00 Close:** "We're not building another chatbot. We're building the bridge between a government notice and a citizen's next action — in the language they think in."

**Submission checklist:** live link · video URL · <250-word summary (incl. AI-build process) · mock credentials shown in-product · README with honesty + GPT-comparison tables.

---

## 18. Risks & mitigations (top line)

Scope creep → §3 ladder + Day-4 10 AM freeze · "works on my phone" bias → stranger test · fragile external pages → in-app Source Panel first · weak Codex evidence → BUILD_LOG discipline + named example · low OpenAI balance → dev-time-only spend + DEMO_MODE · wrong grounding → confidence floor + visible provenance + prompt confinement + retrieval tests · demo flakiness → static-first serving + kill-the-key drills · legal accuracy → Day-3 manual verification · video overrun → locked script, one-take hero · deploy surprises → live from Day 0, every day ends deployed.

---

*Tax Mitra 🇮🇳 — Notice → Understand → Answer → Prepare → Review → Act. AI explains. Rules decide. Humans approve.*

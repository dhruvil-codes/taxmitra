# Tax Mitra — Build Log

Honest, timestamped record of how this prototype was built with AI assistance.
Categories: **[G] AI-generated** · **[R] human-reviewed** · **[X] human-changed/rejected** (+ why).

This log backs the "How this was built" section of the README and the hackathon
submission. The substantial named example for judges is the rules-engine test
suite (2026-08-24, below).

---

## 2026-08-24 (Day 0)

- **[G]** Project skeleton, README, .gitignore, PRD (docs/PRD.md). *Reviewed before commit; PRD structure adjusted by hand to fold in mentor feedback on scope, Codex evidence, citation provenance, refusal demo, and final-action screen.*
- **[G]** Rules engine, all modules (`app/rules/`): notice classification, statutory deadlines, bilingual guided-question trees, personalized checklists, 27-combination response-path resolver, refusal payloads. **[R]** Every path headline/guidance string read line-by-line for Hindi accuracy and plain-language tone; several Hindi sentences shortened by hand.
- **[G]** Synthetic data: `citizens.json`, `notices.json` (143(1)(a) hero + s.148 unsupported), `draft_templates.json` (5 response letters). **[R]** Official notice wording checked against the structure of real 143(1) intimations; explicitly labeled fictional (DIN-DEMO, "Demo Bharat Bank").
- **[G]** Knowledge corpus (12 chunks, `verification: pending`). **[X]** Automated fetching of `.gov.in` sources was attempted and blocked (bot protection) — decision: ship accurate summaries marked *pending* + Day-3 manual verification pass rather than unverifiable "verbatim" claims.
- **[G]** FastAPI app: routers (notices / workflow / ai), data store, config (env-driven models — explicit requirement: no hardcoded model names), AI cache with DEMO_MODE, corpus loader + retriever with confidence floor.
- **[G + R]** **Pytest suite (34 tests) — the named Codex-evidence example.** AI-generated tests for: deadline math and status boundaries; classification table incl. RC support scope; response-path totality across all 27 answer combinations; determinism; evidence overlay; checklist id integrity; draft slot-filling; API contract (happy path, 422s, refusal payload, bilingual explanations with citations); DEMO_MODE kill-the-key drills. **[R]** Two AI-introduced bugs were caught by this suite and fixed by hand: (1) `questions_payload` imported from the wrong module; (2) corpus loader dropped the frontmatter `id` field, silently zeroing all citations — the citation assertions caught it. Both fixes + regressions verified by re-running the suite. **[X]** One AI-generated test file (test_demo_mode.py) initially referenced a nonexistent helper module; rewritten by hand before first run.
- Result: **34/34 tests passing** on Python 3.11.9.

## Environment

- Python 3.11.9, Node 24.19.0, npm 11.17.0 (Windows / Git Bash).
- Dev deps installed globally on the machine for the prototype (no venv in repo).

## 2026-08-24 (Day 0/1 continued — evening session)

- **[G]** Frontend complete: Vite + React 18 + TS + Tailwind v4. All screens: Landing (four answers + "Why not just ChatGPT?" table), mock Login, Dashboard (deadline chips), Understand (plain language + "what this does NOT mean" + reasons + collapsible official text + CitationChips → in-app SourcePanel with verification status), Journey (3 guided questions → personalized checklist with "why do I need this" → editable draft → final review → **final-action screen** with official portal button, copy-draft, and the "Tax Mitra has not submitted your response" boundary), Unsupported refusal screen. EN/हिं instant toggle everywhere; journey state persists in localStorage. **[R]** Caught and hand-fixed an AI-leftover nonsense expression in the Dashboard title rendering; wired locale into card titles.
- **[G]** `scripts/build_kb.py` (corpus → vectors.json), `scripts/pregenerate.py` (grounded explanations → static fallbacks, dev-time spend only), `Procfile`, `.env.example`.
- **[X]** AI-generated SPA mount used an invalid `mount(html=...)` kwarg — caught in the E2E check, fixed by hand to `StaticFiles(directory=...)`.
- **Verification:** `npm run build` clean (63 KB gzipped — low-bandwidth friendly). TestClient E2E: SPA served at `/` (200, text/html), Hindi explanation served static with 4 provenance citations, resolve → `disagree_already_reported` + checklist + deadline + boundary line, s.148 refusal payload OK. **34/34 pytest passing.**

## 2026-08-25 (Day 1/2 — backend hardening pass)

Scope: backend only; frontend handed to the human (contract: `docs/FRONTEND_CONTRACT.md`).

- **[G]** `knowledge/lexical.py` — IDF-weighted lexical retriever over the same corpus (tokenizer keeps section refs like `143(1)(a)` whole; EN+HI stopwords). Exists so the confidence floor is enforceable with **no** vectors.json and **no** API key. **[R]** First suite run caught a missing stopword (`section` was asserted filtered but wasn't in the list) — fixed by hand, not by weakening the test.
- **[G]** `knowledge/grounding.py` — `ground()` prefers embeddings, degrades to lexical, and forces lexical in DEMO_MODE so the demo never touches the network **including embeddings** (previous kill-the-key drill only exploded the chat provider — now the embedder too).
- **[G]** `routers/ai.py` rewrite — every explanation now reports `grounding {method, confidence, below_floor}`; corrected `source`/`degraded` semantics (static is the designed path, `degraded` only for stale-cache-while-live-off).
- **[G]** `main.py` hardening — GZip, security headers, request logging, SPA path-traversal containment, enriched `/api/health` (retrieval method, static-fallback count, and a `static_integrity` self-check that every static citation id resolves in the corpus — regression guard for the Day-0 dropped-id bug class).
- **[X]** AI draft of the new `/api/ai` endpoint used a bottom-of-file late import for `AIUnavailableError` with a false "avoids a cycle" justification — import cycle didn't exist; moved to the top by hand.
- **[G + X]** Bilingual `income_source`: AI first pass left raw English phrases mid-sentence in Hindi output ("जो interest income reported by... ने दी थी") and a doubled verb in English ("information that *interest income reported by X* reported to it"). Fixed by making the field `{en, hi}` in data, locale-aware `render_text`, and rephrasing both fallback openers by hand. Draft templates stay English (official letters).
- **[G]** New tests (+13 → **47/47**): lexical ranking/refusal/top-k, grounding method reporting, health dashboard fields, security headers, 404 matrix across all four id-bearing endpoints, invalid locale 422s, non-string-answer 422 (not 500), locale-appropriate income_source regression.
- **Live E2E (DEMO_MODE=true):** health 200 with `static_integrity: ok`; Hindi explanation static + lexical-grounded (0.349, above floor) + 4 citations; invalid locale → 422; SPA gzip 575 B index. Committed and pushed as `e8b25bd`.


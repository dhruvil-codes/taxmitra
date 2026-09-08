# Tax Mitra V2

Tax Mitra is an independent bilingual prototype that helps taxpayers understand an Income Tax communication, prepare grounded explanations and documents, review a response, and complete the final handoff themselves. It never submits to a government portal automatically.

## Universal Tax Notice Engine

The engine follows:

`PDF validation -> page-aware text/OCR extraction -> grounded classification -> workflow registry -> minimum questions -> evidence mapping -> response draft -> human review -> official portal`

The registry is extensible and covers return/filing, processing, scrutiny/information, rectification, demand/refund, reassessment, penalty and unknown communications. `143(1)(a)`, `143(1)`, `142(1)`, `133(6)`, Section 154, tax-credit mismatch, Section 245/outstanding-demand responses, and grounded AO clarification responses are guided workflows; `139(9)` remains partial support and stops before unsupported legal drafting. Generic sectionless AO/Income Tax Authority requests are partial support when requests are grounded. Refund communications remain explanation-only. Reassessment, penalty, ambiguous classification, weak extraction, weak grounding, unsupported notices, missing information and uncertain answers safe-stop with useful facts and official next steps.

AI explains and drafts, deterministic rules decide, and a human approves. Official portal handoff is guidance only.

## PDF and OCR

Native PDF text is extracted first. OCR runs only for sparse pages, so mixed PDFs retain native text on usable pages and OCR provenance on scanned pages. Page numbers, original wording, confidence, warnings and source locations remain available to classification and workflows. The production `Dockerfile` installs `tesseract-ocr` and `tesseract-ocr-hin` and verifies both languages during image build. OCR output is never authoritative without confirmation.

## Questions and evidence

The backend owns the question plan. It asks only questions whose answers can change the safe next action, supports conditional follow-ups, and preserves `Not sure` as a distinct state. Known document requests appear in the evidence checklist instead of becoming repetitive availability questions. Evidence items retain request context, reason and grounding status; pending sources are not labelled verified.

## API endpoints

- `GET /api/workflows`, `POST /api/workflows/classify`, `POST /api/workflows/extract`
- `GET /api/notices/{notice_id}/workflow`
- `GET /api/workflow/questions/{notice_id}`, `POST /api/workflow/resolve`
- `POST /api/scrutiny/extract`, `POST /api/scrutiny/confirm`
- `GET /api/scrutiny/{notice_id}/requests`
- `GET /api/scrutiny/{notice_id}/question-plan`, `POST /api/scrutiny/question-plan`
- `POST /api/scrutiny/resolve-minimum`, `POST /api/scrutiny/{notice_id}/review-minimum`
- `POST /api/scrutiny/{notice_id}/evidence`, `POST /api/scrutiny/{notice_id}/review`

Existing 143(1)(a) and 142(1) contracts remain available for compatibility. The frontend renders generic workflow metadata and does not recreate backend decision logic. Tax Mitra can process and understand Income Tax communications across supported categories, guide taxpayers through verified workflows, and safely stop when a case is unsupported, ambiguous or too risky to automate.

## Development and validation

```powershell
cd backend
python -m pytest
cd ..\frontend
npm install
npm run test
npm run build
```

The repository currently contains 98 backend tests plus the frontend Vitest suite (3 tests). Fixtures cover native, scanned and mixed PDFs, page provenance, tables, long notices, nested requests, Hindi and English text, poor OCR, malformed, empty and password-protected files. Uploaded documents are processed for the current session only; document contents are not logged or persisted by the workflow.

## Production Deployment
- Backend: Railway (https://web-production-cfee8.up.railway.app)
- Frontend: Vercel (https://taxmitra.bydhruvil.in)
- Last deployment sync: 2026-09-08

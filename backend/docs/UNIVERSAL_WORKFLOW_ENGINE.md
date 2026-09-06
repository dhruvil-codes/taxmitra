# Universal Tax Notice Engine

Tax Mitra routes every extracted Income Tax communication through
`app.workflows.registry`. Each workflow declares an explicit capability:
`SUPPORTED`, `PARTIAL_SUPPORT`, `EXPLANATION_ONLY`, or `SAFE_STOP`.

Current capability map:

- `income_mismatch_143_1a` and `scrutiny_142_1`: fully guided, backward-compatible workflows.
- `defective_return_139_9` and general `income_intimation_143_1`: partial guided workflows with confirmed requests and no unsafe legal drafting.
- 133(6), 154, TDS mismatch, 245, outstanding demand/refund, and AO clarification: explanation-only.
- Reassessment, penalty, ambiguous, and unknown communications: useful safe-stop.

The backend owns classification and workflow decisions. Classification returns
confidence, grounding state, reason, and evidence. Low-confidence or ambiguous
cases stop safely. Partial, explanation-only, and safe-stop cases never receive
an automatic response or government submission.

## Universal contract

The ingestion path is validation -> page-aware text/OCR -> normalization ->
classification -> registry lookup -> capability check -> workflow or safe stop.
Structured requests preserve original wording, page provenance, confidence,
and request-specific evidence. Human confirmation is required before extracted
facts are used. Question planning must preserve `Not sure` as distinct from
`No`, and evidence mapping is request-scoped.

## Generic API

- `GET /api/workflows` returns the registry catalog.
- `POST /api/workflows/classify` returns category, capability, confidence,
  grounding status, evidence, and safe-stop reason.
- `POST /api/workflows/extract` runs the universal PDF boundary.
- `POST /api/workflows/confirm` confirms extracted requests and routes to the
  workflow entry point when permitted.
- `GET /api/notices/{notice_id}/workflow` returns the contract for an existing
  notice. Legacy `/api/workflow/*` and `/api/scrutiny/*` routes remain available.

Official portal handoff is guidance only; Tax Mitra never submits for a
taxpayer.

# Universal Tax Notice Engine

Tax Mitra routes every extracted Income Tax communication through
`app.workflows.registry`. Each workflow declares an explicit capability:
`SUPPORTED`, `PARTIAL_SUPPORT`, `EXPLANATION_ONLY`, or `SAFE_STOP`.

Current capability map:

- `income_mismatch_143_1a` and `scrutiny_142_1`: fully guided, backward-compatible workflows.
- `defective_return_139_9`: partial guided workflow with confirmed defects and no unsafe legal drafting.
- `income_intimation_143_1`: guided final-processing workflow that explains refund, demand, tax-calculation, tax-credit and no-action outcomes and routes only to verified taxpayer-controlled portal actions.
- `rectification_154` and `tax_credit_tds_mismatch`: guided rectification and credit-mismatch workflows with record-based eligibility, evidence, taxpayer/deductor routing, and safe-stop boundaries.
- `demand_adjustment_245` and `outstanding_tax_demand`: guided demand-response workflow covering correct, paid, fully disputed, and partially disputed demand states; payment and submission remain on the official portal.
- `scrutiny_information_133_6`: guided request-by-request information response with partial availability, evidence mapping, and official e-Proceedings/Comply to Notice handoff.
- `authority_information_request`: section-independent partial-support fallback for grounded Assessing Officer or other Income Tax authority information requests.
- `ao_notice_clarification`: distinct guided clarification response using the shared request/evidence engine; it does not become 142(1) scrutiny.
- Refund communications and AO clarification: explanation-only. Section 245 and outstanding demand are guided demand-response workflows; refund reissue remains explanation-only.
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
